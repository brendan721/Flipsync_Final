"""
Approval Integration Service for FlipSync

This service bridges the gap between conversational agents and the Decision Pipeline,
automatically creating approval workflows when agents set requires_approval=True.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.base_conversational_agent import UnifiedAgentResponse
from fs_agt_clean.core.coordination.decision.models import (
    Decision,
    DecisionConfidence,
    DecisionStatus,
    DecisionType,
)
from fs_agt_clean.core.coordination.decision.pipeline import StandardDecisionPipeline
from fs_agt_clean.database.models.unified_agent import UnifiedAgentDecision
from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository

# Import decision pipeline components with error handling
try:
    from fs_agt_clean.core.coordination.decision import (
        InMemoryDecisionMaker,
        InMemoryDecisionTracker,
        InMemoryFeedbackProcessor,
        InMemoryLearningEngine,
        RuleBasedValidator,
    )
except ImportError:
    # Fallback imports for development
    InMemoryDecisionMaker = None
    RuleBasedValidator = None
    InMemoryDecisionTracker = None
    InMemoryFeedbackProcessor = None
    InMemoryLearningEngine = None

logger = logging.getLogger(__name__)


class ApprovalIntegrationService:
    """
    Service that integrates conversational agent responses with the Decision Pipeline
    for approval workflows.
    """

    def __init__(self, agent_repository: Optional[UnifiedAgentRepository] = None):
        """Initialize the approval integration service."""
        self.agent_repository = agent_repository
        self.decision_pipeline = None
        self._initialize_decision_pipeline()

        # Approval routing configuration
        self.approval_routing = {
            "content": {
                "auto_approve_threshold": 0.9,
                "requires_human_approval": ["template_changes", "brand_guidelines"],
                "escalation_threshold": 0.5,
            },
            "logistics": {
                "auto_approve_threshold": 0.85,
                "requires_human_approval": ["carrier_changes", "cost_optimization"],
                "escalation_threshold": 0.6,
            },
            "executive": {
                "auto_approve_threshold": 0.8,
                "requires_human_approval": ["strategic_decisions", "budget_changes"],
                "escalation_threshold": 0.7,
            },
        }

        logger.info("Approval Integration Service initialized")

    def _initialize_decision_pipeline(self):
        """Initialize the decision pipeline for approval workflows."""
        try:
            if all(
                [
                    InMemoryDecisionMaker,
                    RuleBasedValidator,
                    InMemoryDecisionTracker,
                    InMemoryFeedbackProcessor,
                    InMemoryLearningEngine,
                ]
            ):

                # Import EventPublisher for Decision Pipeline components
                from fs_agt_clean.core.coordination.event_system import create_publisher

                # Create EventPublisher for Decision Pipeline components
                publisher = create_publisher(source_id="approval_decision_pipeline")

                # Create decision pipeline components with required parameters
                decision_maker = InMemoryDecisionMaker(
                    maker_id="approval_decision_maker"
                )
                decision_validator = RuleBasedValidator(
                    validator_id="approval_decision_validator"
                )
                decision_tracker = InMemoryDecisionTracker(
                    tracker_id="approval_decision_tracker", publisher=publisher
                )
                feedback_processor = InMemoryFeedbackProcessor(
                    processor_id="approval_feedback_processor", publisher=publisher
                )
                learning_engine = InMemoryLearningEngine(
                    engine_id="approval_learning_engine", publisher=publisher
                )

                # Create the pipeline with all required parameters
                self.decision_pipeline = StandardDecisionPipeline(
                    pipeline_id="approval_pipeline",
                    decision_maker=decision_maker,
                    decision_validator=decision_validator,
                    decision_tracker=decision_tracker,
                    feedback_processor=feedback_processor,
                    learning_engine=learning_engine,
                    publisher=publisher,
                )

                logger.info(
                    "✅ Decision pipeline initialized successfully for approval workflows"
                )
            else:
                logger.warning(
                    "Decision pipeline components not available, using fallback approval system"
                )
                self.decision_pipeline = None

        except Exception as e:
            logger.error(f"Error initializing decision pipeline: {e}")
            logger.info("Using fallback approval system")
            self.decision_pipeline = None

    async def process_agent_response(
        self,
        agent_response: UnifiedAgentResponse,
        user_id: str,
        conversation_id: str,
        original_message: str,
    ) -> Dict[str, Any]:
        """
        Process an agent response and create approval workflow if needed.

        Args:
            agent_response: The agent response to process
            user_id: UnifiedUser identifier
            conversation_id: Conversation identifier
            original_message: Original user message

        Returns:
            Dictionary with approval workflow information
        """
        try:
            # Check if approval is required
            requires_approval = agent_response.metadata.get("requires_approval", False)

            if not requires_approval:
                return {
                    "approval_required": False,
                    "response": agent_response.content,
                    "agent_type": agent_response.agent_type,
                }

            # Create approval workflow
            approval_workflow = await self._create_approval_workflow(
                agent_response, user_id, conversation_id, original_message
            )

            # Store in database if repository is available
            if self.agent_repository:
                await self._store_approval_decision(approval_workflow, agent_response)

            return {
                "approval_required": True,
                "approval_id": approval_workflow["approval_id"],
                "decision_type": approval_workflow["decision_type"],
                "confidence": agent_response.confidence,
                "auto_approve": approval_workflow["auto_approve"],
                "escalation_required": approval_workflow["escalation_required"],
                "response": self._create_approval_response(
                    approval_workflow, agent_response
                ),
                "agent_type": agent_response.agent_type,
                "workflow_data": approval_workflow,
            }

        except Exception as e:
            logger.error(f"Error processing agent response for approval: {e}")
            return {
                "approval_required": False,
                "response": agent_response.content,
                "agent_type": agent_response.agent_type,
                "error": str(e),
            }

    async def _create_approval_workflow(
        self,
        agent_response: UnifiedAgentResponse,
        user_id: str,
        conversation_id: str,
        original_message: str,
    ) -> Dict[str, Any]:
        """Create an approval workflow for the agent response."""
        approval_id = str(uuid.uuid4())
        agent_type = agent_response.agent_type

        # Determine decision type based on agent response metadata
        decision_type = self._determine_decision_type(agent_response)

        # Get approval configuration for this agent type
        config = self.approval_routing.get(agent_type, {})
        auto_approve_threshold = config.get("auto_approve_threshold", 0.8)
        escalation_threshold = config.get("escalation_threshold", 0.6)

        # Determine approval strategy
        auto_approve = (
            agent_response.confidence >= auto_approve_threshold
            and decision_type not in config.get("requires_human_approval", [])
        )

        escalation_required = agent_response.confidence < escalation_threshold

        # Create workflow data
        workflow = {
            "approval_id": approval_id,
            "agent_type": agent_type,
            "decision_type": decision_type,
            "confidence": agent_response.confidence,
            "auto_approve": auto_approve,
            "escalation_required": escalation_required,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "original_message": original_message,
            "agent_response_data": agent_response.metadata.get("data", {}),
            "created_at": datetime.now(timezone.utc),
            "status": "auto_approved" if auto_approve else "pending_approval",
        }

        # Create decision pipeline entry if available
        if self.decision_pipeline:
            await self._create_pipeline_decision(workflow, agent_response)

        return workflow

    def _determine_decision_type(self, agent_response: UnifiedAgentResponse) -> str:
        """Determine the decision type based on agent response."""
        agent_type = agent_response.agent_type
        metadata = agent_response.metadata

        # Extract decision type from metadata
        if "request_type" in metadata:
            request_type = metadata["request_type"]

            if agent_type == "content":
                type_mapping = {
                    "generate": "content_generation",
                    "optimize": "content_optimization",
                    "template": "template_changes",
                    "analyze": "content_analysis",
                }
                return type_mapping.get(request_type, "content_general")

            elif agent_type == "logistics":
                type_mapping = {
                    "shipping": "shipping_optimization",
                    "inventory": "inventory_rebalancing",
                    "tracking": "tracking_management",
                    "optimization": "logistics_optimization",
                }
                return type_mapping.get(request_type, "logistics_general")

            elif agent_type == "executive":
                return "strategic_decision"

        # Fallback to agent type
        return f"{agent_type}_decision"

    async def _create_pipeline_decision(
        self, workflow: Dict[str, Any], agent_response: UnifiedAgentResponse
    ):
        """Create a decision in the decision pipeline."""
        try:
            context = {
                "approval_id": workflow["approval_id"],
                "agent_type": workflow["agent_type"],
                "user_id": workflow["user_id"],
                "conversation_id": workflow["conversation_id"],
                "confidence": workflow["confidence"],
                "decision_type": workflow["decision_type"],
            }

            options = [
                {
                    "id": "approve",
                    "action": "approve",
                    "reasoning": "UnifiedAgent recommendation approved",
                },
                {
                    "id": "reject",
                    "action": "reject",
                    "reasoning": "UnifiedAgent recommendation rejected",
                },
                {
                    "id": "modify",
                    "action": "modify",
                    "reasoning": "UnifiedAgent recommendation requires modification",
                },
            ]

            # Make decision through pipeline
            decision = await self.decision_pipeline.make_decision(context, options)
            workflow["pipeline_decision_id"] = decision.metadata.decision_id

        except Exception as e:
            logger.error(f"Error creating pipeline decision: {e}")

    async def _store_approval_decision(
        self, workflow: Dict[str, Any], agent_response: UnifiedAgentResponse
    ):
        """Store the approval decision in the database."""
        try:
            if not self.agent_repository:
                return

            # Create UnifiedAgentDecision record
            decision_record = UnifiedAgentDecision(
                agent_id=agent_response.metadata.get("agent_id", "unknown"),
                decision_type=workflow["decision_type"],
                parameters={
                    "original_message": workflow["original_message"],
                    "agent_response_data": workflow["agent_response_data"],
                    "approval_workflow": workflow,
                },
                confidence=workflow["confidence"],
                rationale=f"UnifiedAgent recommendation: {agent_response.content[:200]}...",
                status="approved" if workflow["auto_approve"] else "pending",
            )

            # Store in database
            await self.agent_repository.create_decision(decision_record)

        except Exception as e:
            logger.error(f"Error storing approval decision: {e}")

    def _create_approval_response(
        self, workflow: Dict[str, Any], agent_response: UnifiedAgentResponse
    ) -> str:
        """Create a response message for approval workflows."""
        if workflow["auto_approve"]:
            return f"{agent_response.content}\n\n✅ **Auto-approved** (Confidence: {workflow['confidence']:.1%})"

        elif workflow["escalation_required"]:
            return f"{agent_response.content}\n\n⚠️ **Requires review** - Low confidence ({workflow['confidence']:.1%}). This recommendation has been escalated for human approval."

        else:
            return f"{agent_response.content}\n\n⏳ **Pending approval** - This recommendation requires approval before implementation. Approval ID: `{workflow['approval_id']}`"

    async def approve_decision(
        self, approval_id: str, approved_by: str
    ) -> Dict[str, Any]:
        """Approve a pending decision."""
        try:
            # Update decision status
            if self.agent_repository:
                await self.agent_repository.update_decision_status(
                    approval_id, "approved", approved_by
                )

            # Process feedback through decision pipeline
            if self.decision_pipeline:
                feedback_data = {
                    "outcome": "approved",
                    "approved_by": approved_by,
                    "timestamp": datetime.now(timezone.utc),
                }
                # Note: Would need decision_id from workflow to process feedback

            return {
                "status": "approved",
                "approval_id": approval_id,
                "approved_by": approved_by,
                "timestamp": datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.error(f"Error approving decision {approval_id}: {e}")
            raise

    async def reject_decision(
        self, approval_id: str, rejected_by: str, reason: str = None
    ) -> Dict[str, Any]:
        """Reject a pending decision."""
        try:
            # Update decision status
            if self.agent_repository:
                await self.agent_repository.update_decision_status(
                    approval_id, "rejected", rejected_by, reason
                )

            return {
                "status": "rejected",
                "approval_id": approval_id,
                "rejected_by": rejected_by,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.error(f"Error rejecting decision {approval_id}: {e}")
            raise
