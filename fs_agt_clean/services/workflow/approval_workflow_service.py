"""
Approval Workflow Service for FlipSync.

This service provides real-time approval workflow management including:
- Multi-step approval processes
- Real-time notifications via WebSocket
- Approval request tracking and management
- Timeout handling and escalation
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Note: Enhanced WebSocket manager is temporarily disabled
# from fs_agt_clean.core.websocket.enhanced_websocket_manager import (
#     enhanced_websocket_manager, EventType
# )

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Approval workflow status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ApprovalPriority(str, Enum):
    """Approval priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApprovalType(str, Enum):
    """Types of approval requests."""

    LISTING_PUBLISH = "listing_publish"
    BULK_OPERATION = "bulk_operation"
    PRICE_CHANGE = "price_change"
    CATEGORY_CHANGE = "category_change"
    MARKETPLACE_SYNC = "marketplace_sync"
    AI_RECOMMENDATION = "ai_recommendation"
    SUBSCRIPTION_CHANGE = "subscription_change"


class ApprovalRequest:
    """Approval request model."""

    def __init__(
        self,
        request_id: str,
        requester_id: str,
        approval_type: ApprovalType,
        title: str,
        description: str,
        data: Dict[str, Any],
        approvers: List[str],
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        timeout_minutes: int = 60,
        requires_all_approvers: bool = False,
    ):
        self.request_id = request_id
        self.requester_id = requester_id
        self.approval_type = approval_type
        self.title = title
        self.description = description
        self.data = data
        self.approvers = approvers
        self.priority = priority
        self.timeout_minutes = timeout_minutes
        self.requires_all_approvers = requires_all_approvers

        # Status tracking
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.timeout_at = self.created_at + timedelta(minutes=timeout_minutes)
        self.completed_at: Optional[datetime] = None

        # Approval tracking
        self.approvals: Dict[str, Dict[str, Any]] = {}  # approver_id -> approval_data
        self.rejections: Dict[str, Dict[str, Any]] = {}  # approver_id -> rejection_data

        # Metadata
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "requester_id": self.requester_id,
            "approval_type": self.approval_type.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "approvers": self.approvers,
            "priority": self.priority.value,
            "timeout_minutes": self.timeout_minutes,
            "requires_all_approvers": self.requires_all_approvers,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "timeout_at": self.timeout_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "approvals": self.approvals,
            "rejections": self.rejections,
            "metadata": self.metadata,
        }

    def is_approved(self) -> bool:
        """Check if request is approved."""
        if self.requires_all_approvers:
            return len(self.approvals) == len(self.approvers)
        else:
            return len(self.approvals) > 0

    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        if self.requires_all_approvers:
            return len(self.rejections) > 0  # Any rejection blocks approval
        else:
            return len(self.rejections) >= len(self.approvers) - len(self.approvals)

    def is_expired(self) -> bool:
        """Check if request has expired."""
        return datetime.now(timezone.utc) > self.timeout_at


class ApprovalWorkflowService:
    """
    Approval workflow service with real-time notifications.

    This service provides:
    - Multi-step approval process management
    - Real-time WebSocket notifications
    - Approval request tracking and persistence
    - Timeout handling and escalation
    """

    def __init__(self):
        """Initialize the approval workflow service."""
        self.active_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: Dict[str, ApprovalRequest] = {}

        # Background task for timeout monitoring
        self._timeout_task: Optional[asyncio.Task] = None
        self._start_timeout_monitor()

        logger.info("Approval Workflow Service initialized")

    def _start_timeout_monitor(self):
        """Start background task to monitor timeouts."""
        try:
            self._timeout_task = asyncio.create_task(self._monitor_timeouts())
        except Exception as e:
            logger.error(f"Error starting timeout monitor: {e}")

    async def _monitor_timeouts(self):
        """Monitor approval request timeouts."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                expired_requests = []
                for request_id, request in self.active_requests.items():
                    if (
                        request.is_expired()
                        and request.status == ApprovalStatus.PENDING
                    ):
                        expired_requests.append(request_id)

                for request_id in expired_requests:
                    await self._handle_timeout(request_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")

    async def create_approval_request(
        self,
        requester_id: str,
        approval_type: ApprovalType,
        title: str,
        description: str,
        data: Dict[str, Any],
        approvers: List[str],
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        timeout_minutes: int = 60,
        requires_all_approvers: bool = False,
    ) -> str:
        """
        Create a new approval request.

        Args:
            requester_id: ID of the user requesting approval
            approval_type: Type of approval request
            title: Request title
            description: Request description
            data: Request data and context
            approvers: List of approver user IDs
            priority: Request priority
            timeout_minutes: Timeout in minutes
            requires_all_approvers: Whether all approvers must approve

        Returns:
            Request ID
        """
        try:
            # Generate request ID
            request_id = str(uuid4())

            # Create approval request
            request = ApprovalRequest(
                request_id=request_id,
                requester_id=requester_id,
                approval_type=approval_type,
                title=title,
                description=description,
                data=data,
                approvers=approvers,
                priority=priority,
                timeout_minutes=timeout_minutes,
                requires_all_approvers=requires_all_approvers,
            )

            # Store request
            self.active_requests[request_id] = request

            # Notify approvers via WebSocket
            await self._notify_approval_request_created(request)

            logger.info(
                f"Created approval request: {request_id} for {approval_type.value}"
            )
            return request_id

        except Exception as e:
            logger.error(f"Error creating approval request: {e}")
            return ""

    async def approve_request(
        self,
        request_id: str,
        approver_id: str,
        comments: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Approve an approval request.

        Args:
            request_id: Request ID
            approver_id: ID of the approver
            comments: Optional approval comments
            metadata: Optional approval metadata

        Returns:
            True if approval was successful
        """
        try:
            request = self.active_requests.get(request_id)
            if not request:
                logger.warning(f"Approval request not found: {request_id}")
                return False

            # Check if user is authorized to approve
            if approver_id not in request.approvers:
                logger.warning(
                    f"UnifiedUser {approver_id} not authorized to approve {request_id}"
                )
                return False

            # Check if already approved by this user
            if approver_id in request.approvals:
                logger.warning(
                    f"Request {request_id} already approved by {approver_id}"
                )
                return False

            # Check if request is still pending
            if request.status != ApprovalStatus.PENDING:
                logger.warning(
                    f"Request {request_id} is not pending (status: {request.status})"
                )
                return False

            # Record approval
            request.approvals[approver_id] = {
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "comments": comments,
                "metadata": metadata or {},
            }

            # Check if request is now fully approved
            if request.is_approved():
                request.status = ApprovalStatus.APPROVED
                request.completed_at = datetime.now(timezone.utc)

                # Move to completed requests
                self.completed_requests[request_id] = request
                del self.active_requests[request_id]

                # Notify completion
                await self._notify_approval_completed(request)
            else:
                # Notify partial approval
                await self._notify_approval_progress(request, approver_id, "approved")

            logger.info(f"Request {request_id} approved by {approver_id}")
            return True

        except Exception as e:
            logger.error(f"Error approving request: {e}")
            return False

    async def reject_request(
        self,
        request_id: str,
        approver_id: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Reject an approval request.

        Args:
            request_id: Request ID
            approver_id: ID of the approver
            reason: Rejection reason
            metadata: Optional rejection metadata

        Returns:
            True if rejection was successful
        """
        try:
            request = self.active_requests.get(request_id)
            if not request:
                logger.warning(f"Approval request not found: {request_id}")
                return False

            # Check if user is authorized to reject
            if approver_id not in request.approvers:
                logger.warning(
                    f"UnifiedUser {approver_id} not authorized to reject {request_id}"
                )
                return False

            # Check if already rejected by this user
            if approver_id in request.rejections:
                logger.warning(
                    f"Request {request_id} already rejected by {approver_id}"
                )
                return False

            # Check if request is still pending
            if request.status != ApprovalStatus.PENDING:
                logger.warning(
                    f"Request {request_id} is not pending (status: {request.status})"
                )
                return False

            # Record rejection
            request.rejections[approver_id] = {
                "rejected_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "metadata": metadata or {},
            }

            # Check if request is now rejected
            if request.is_rejected():
                request.status = ApprovalStatus.REJECTED
                request.completed_at = datetime.now(timezone.utc)

                # Move to completed requests
                self.completed_requests[request_id] = request
                del self.active_requests[request_id]

                # Notify rejection
                await self._notify_approval_rejected(request)
            else:
                # Notify partial rejection
                await self._notify_approval_progress(request, approver_id, "rejected")

            logger.info(f"Request {request_id} rejected by {approver_id}")
            return True

        except Exception as e:
            logger.error(f"Error rejecting request: {e}")
            return False

    async def _handle_timeout(self, request_id: str):
        """Handle approval request timeout."""
        try:
            request = self.active_requests.get(request_id)
            if not request:
                return

            request.status = ApprovalStatus.TIMEOUT
            request.completed_at = datetime.now(timezone.utc)

            # Move to completed requests
            self.completed_requests[request_id] = request
            del self.active_requests[request_id]

            # Notify timeout
            await self._notify_approval_timeout(request)

            logger.info(f"Request {request_id} timed out")

        except Exception as e:
            logger.error(f"Error handling timeout: {e}")

    async def _notify_approval_request_created(self, request: ApprovalRequest):
        """Notify approvers of new approval request - DISABLED."""
        # WebSocket notifications temporarily disabled
        logger.info(
            f"Would notify approval request created: {request.request_id} (WebSocket disabled)"
        )

    async def _notify_approval_progress(
        self, request: ApprovalRequest, approver_id: str, action: str
    ):
        """Notify of approval progress - DISABLED."""
        # WebSocket notifications temporarily disabled
        logger.info(
            f"Would notify approval progress: {request.request_id} - {action} by {approver_id} (WebSocket disabled)"
        )

    async def _notify_approval_completed(self, request: ApprovalRequest):
        """Notify of approval completion - DISABLED."""
        # WebSocket notifications temporarily disabled
        logger.info(
            f"Would notify approval completed: {request.request_id} (WebSocket disabled)"
        )

    async def _notify_approval_rejected(self, request: ApprovalRequest):
        """Notify of approval rejection - DISABLED."""
        # WebSocket notifications temporarily disabled
        logger.info(
            f"Would notify approval rejected: {request.request_id} (WebSocket disabled)"
        )

    async def _notify_approval_timeout(self, request: ApprovalRequest):
        """Notify of approval timeout - DISABLED."""
        # WebSocket notifications temporarily disabled
        logger.info(
            f"Would notify approval timeout: {request.request_id} (WebSocket disabled)"
        )

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID."""
        return self.active_requests.get(request_id) or self.completed_requests.get(
            request_id
        )

    def get_user_requests(
        self, user_id: str, include_completed: bool = False
    ) -> List[ApprovalRequest]:
        """Get approval requests for a user."""
        requests = []

        # Active requests
        for request in self.active_requests.values():
            if user_id in request.approvers or user_id == request.requester_id:
                requests.append(request)

        # Completed requests if requested
        if include_completed:
            for request in self.completed_requests.values():
                if user_id in request.approvers or user_id == request.requester_id:
                    requests.append(request)

        return sorted(requests, key=lambda r: r.created_at, reverse=True)

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        return {
            "active_requests": len(self.active_requests),
            "completed_requests": len(self.completed_requests),
            "total_requests": len(self.active_requests) + len(self.completed_requests),
            "timeout_monitor_running": self._timeout_task is not None
            and not self._timeout_task.done(),
            "request_types": self._get_request_type_stats(),
            "priority_distribution": self._get_priority_stats(),
        }

    def _get_request_type_stats(self) -> Dict[str, int]:
        """Get request type statistics."""
        stats = {}
        all_requests = list(self.active_requests.values()) + list(
            self.completed_requests.values()
        )

        for request in all_requests:
            request_type = request.approval_type.value
            stats[request_type] = stats.get(request_type, 0) + 1

        return stats

    def _get_priority_stats(self) -> Dict[str, int]:
        """Get priority distribution statistics."""
        stats = {}
        all_requests = list(self.active_requests.values()) + list(
            self.completed_requests.values()
        )

        for request in all_requests:
            priority = request.priority.value
            stats[priority] = stats.get(priority, 0) + 1

        return stats


# Global approval workflow service instance
approval_workflow_service = ApprovalWorkflowService()
