"""
Sync UnifiedAgent for FlipSync - Cross-Platform Synchronization and Data Coordination

This agent specializes in:
- Cross-platform data synchronization between marketplaces
- Conflict resolution for inventory and pricing discrepancies
- Data validation and consistency checks
- Marketplace-specific data transformation
- Synchronization scheduling and monitoring
- Real-time sync status reporting
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.core.models.marketplace_models import MarketplaceType
from fs_agt_clean.database.repositories.market_repository import MarketRepository

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Status of synchronization operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    PARTIAL = "partial"


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving data conflicts."""

    LATEST_WINS = "latest_wins"
    HIGHEST_PRIORITY = "highest_priority"
    MANUAL_REVIEW = "manual_review"
    MERGE_VALUES = "merge_values"
    MARKETPLACE_SPECIFIC = "marketplace_specific"


@dataclass
class SyncOperation:
    """Represents a synchronization operation."""

    operation_id: str
    source_marketplace: str
    target_marketplaces: List[str]
    data_type: str  # 'inventory', 'pricing', 'listing', 'orders'
    entity_id: str  # SKU, listing ID, etc.
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    conflicts: List[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class DataConflict:
    """Represents a data conflict between marketplaces."""

    conflict_id: str
    entity_id: str
    field_name: str
    marketplace_values: Dict[str, Any]
    resolution_strategy: ConflictResolutionStrategy
    resolved: bool = False
    resolved_value: Any = None
    resolved_at: Optional[datetime] = None


class SyncUnifiedAgent(BaseConversationalUnifiedAgent):
    """
    Sync UnifiedAgent for cross-platform data synchronization and coordination.

    Capabilities:
    - Synchronize inventory levels across marketplaces
    - Coordinate pricing updates between platforms
    - Resolve data conflicts intelligently
    - Monitor sync operations and status
    - Schedule automated synchronization tasks
    - Validate data consistency across platforms
    """

    def __init__(self, agent_id: Optional[str] = None, use_fast_model: bool = True):
        """Initialize the Sync UnifiedAgent."""
        super().__init__(UnifiedAgentRole.LOGISTICS, agent_id, use_fast_model)

        # Sync agent capabilities
        self.capabilities = [
            "cross_platform_sync",
            "conflict_resolution",
            "data_validation",
            "sync_monitoring",
            "automated_scheduling",
            "consistency_checks",
            "marketplace_coordination",
            "real_time_updates",
        ]

        # Active sync operations
        self.active_operations: Dict[str, SyncOperation] = {}
        self.pending_conflicts: Dict[str, DataConflict] = {}

        # Marketplace priorities for conflict resolution
        self.marketplace_priorities = {
            "amazon": 3,
            "ebay": 2,
            "walmart": 2,
            "etsy": 1,
            "facebook": 1,
        }

        # Sync configuration
        self.sync_intervals = {
            "inventory": 300,  # 5 minutes
            "pricing": 600,  # 10 minutes
            "listings": 1800,  # 30 minutes
            "orders": 180,  # 3 minutes
        }

        # Data transformation rules
        self.transformation_rules = {}

        # Initialize database components
        self.database = self._initialize_database()
        self.market_repository = MarketRepository()

        logger.info(f"Sync UnifiedAgent initialized: {self.agent_id}")

    def _initialize_database(self):
        """Initialize database with proper connection string."""
        import os
        from fs_agt_clean.core.db.database import Database
        from fs_agt_clean.core.config.config_manager import ConfigManager

        # Get DATABASE_URL from environment
        database_url = os.getenv("DATABASE_URL")
        if database_url and database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        if not database_url:
            # Fallback to default connection string for Docker
            database_url = "postgresql+asyncpg://postgres:postgres@db:5432/postgres"
            logger.warning(f"Using fallback database connection: {database_url}")

        # Create properly initialized database instance
        config = ConfigManager()
        database = Database(
            config_manager=config,
            connection_string=database_url,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )

        logger.info("Database instance created for SyncUnifiedAgent")
        return database

    async def _ensure_database_initialized(self):
        """Ensure database is initialized before use."""
        if not self.database._session_factory:
            await self.database.initialize()
            logger.info("Database initialized for SyncUnifiedAgent")

    async def synchronize_data(
        self,
        data_type: str,
        entity_id: str,
        source_marketplace: str,
        target_marketplaces: List[str],
        data: Dict[str, Any],
    ) -> SyncOperation:
        """
        Synchronize data across marketplaces.

        Args:
            data_type: Type of data to sync (inventory, pricing, listing, orders)
            entity_id: Identifier for the entity being synced
            source_marketplace: Source marketplace for the data
            target_marketplaces: Target marketplaces to sync to
            data: Data to synchronize

        Returns:
            SyncOperation object tracking the sync process
        """
        operation_id = (
            f"sync_{data_type}_{entity_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        operation = SyncOperation(
            operation_id=operation_id,
            source_marketplace=source_marketplace,
            target_marketplaces=target_marketplaces,
            data_type=data_type,
            entity_id=entity_id,
            status=SyncStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            metadata={"original_data": data},
        )

        self.active_operations[operation_id] = operation

        try:
            operation.status = SyncStatus.IN_PROGRESS

            # Validate source data
            validation_result = await self._validate_data(data_type, data)
            if not validation_result["valid"]:
                operation.status = SyncStatus.FAILED
                operation.error_message = (
                    f"Data validation failed: {validation_result['errors']}"
                )
                return operation

            # Transform data for each target marketplace
            sync_results = []
            conflicts = []

            for target_marketplace in target_marketplaces:
                try:
                    # Transform data for target marketplace
                    transformed_data = await self._transform_data(
                        data, source_marketplace, target_marketplace, data_type
                    )

                    # Check for conflicts with existing data
                    conflict_check = await self._check_conflicts(
                        entity_id, target_marketplace, transformed_data, data_type
                    )

                    if conflict_check["has_conflicts"]:
                        conflicts.extend(conflict_check["conflicts"])
                        # Apply conflict resolution
                        resolved_data = await self._resolve_conflicts(
                            conflict_check["conflicts"], transformed_data
                        )
                        transformed_data = resolved_data

                    # Perform the actual sync
                    sync_result = await self._perform_sync(
                        entity_id, target_marketplace, transformed_data, data_type
                    )
                    sync_results.append(sync_result)

                except Exception as e:
                    logger.error(f"Sync failed for {target_marketplace}: {e}")
                    sync_results.append(
                        {
                            "marketplace": target_marketplace,
                            "success": False,
                            "error": str(e),
                        }
                    )

            # Determine overall operation status
            successful_syncs = [r for r in sync_results if r.get("success", False)]

            if len(successful_syncs) == len(target_marketplaces):
                operation.status = SyncStatus.COMPLETED
            elif len(successful_syncs) > 0:
                operation.status = SyncStatus.PARTIAL
            else:
                operation.status = SyncStatus.FAILED

            if conflicts:
                operation.conflicts = conflicts
                if operation.status == SyncStatus.COMPLETED:
                    operation.status = SyncStatus.CONFLICT

            operation.completed_at = datetime.now(timezone.utc)
            operation.metadata["sync_results"] = sync_results

        except Exception as e:
            logger.error(f"Sync operation failed: {e}")
            operation.status = SyncStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now(timezone.utc)

        return operation

    async def get_sync_status(self, operation_id: str) -> Optional[SyncOperation]:
        """Get the status of a sync operation."""
        return self.active_operations.get(operation_id)

    async def list_active_operations(self) -> List[SyncOperation]:
        """List all active sync operations."""
        return list(self.active_operations.values())

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: ConflictResolutionStrategy,
        manual_value: Any = None,
    ) -> bool:
        """
        Resolve a data conflict.

        Args:
            conflict_id: ID of the conflict to resolve
            resolution_strategy: Strategy to use for resolution
            manual_value: Manual value if using manual resolution

        Returns:
            True if conflict was resolved successfully
        """
        if conflict_id not in self.pending_conflicts:
            return False

        conflict = self.pending_conflicts[conflict_id]

        try:
            if (
                resolution_strategy == ConflictResolutionStrategy.MANUAL_REVIEW
                and manual_value is not None
            ):
                conflict.resolved_value = manual_value
            else:
                conflict.resolved_value = await self._apply_resolution_strategy(
                    conflict, resolution_strategy
                )

            conflict.resolved = True
            conflict.resolved_at = datetime.now(timezone.utc)

            # Remove from pending conflicts
            del self.pending_conflicts[conflict_id]

            logger.info(
                f"Conflict {conflict_id} resolved with strategy {resolution_strategy}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return False

    # Required abstract methods from BaseConversationalUnifiedAgent

    async def _process_response(
        self,
        llm_response: str,
        original_message: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Process the LLM response with sync-specific logic."""
        # Extract sync commands or requests from the response
        if "sync" in original_message.lower():
            # Add sync operation status or recommendations
            active_ops = len(self.active_operations)
            pending_conflicts = len(self.pending_conflicts)

            if active_ops > 0 or pending_conflicts > 0:
                status_info = f"\n\n📊 **Current Sync Status:**\n"
                status_info += f"• Active operations: {active_ops}\n"
                status_info += f"• Pending conflicts: {pending_conflicts}\n"

                if pending_conflicts > 0:
                    status_info += "\n⚠️ **Action Required:** You have pending conflicts that need resolution."

                llm_response += status_info

        return llm_response

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        return {
            "agent_type": "cross_platform_synchronization_specialist",
            "capabilities": self.capabilities,
            "specializations": [
                "Cross-platform data synchronization",
                "Conflict resolution",
                "Data validation and consistency",
                "Marketplace coordination",
            ],
            "supported_marketplaces": list(self.marketplace_priorities.keys()),
            "sync_operations": {
                "active": len(self.active_operations),
                "pending_conflicts": len(self.pending_conflicts),
            },
            "sync_intervals": self.sync_intervals,
        }

    # Helper methods for sync operations

    async def _validate_data(
        self, data_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data before synchronization."""
        errors = []

        # Common validation rules
        if not data:
            errors.append("Data cannot be empty")

        # Data type specific validation
        if data_type == "inventory":
            if "quantity" not in data:
                errors.append("Inventory data must include quantity")
            elif not isinstance(data["quantity"], (int, float)) or data["quantity"] < 0:
                errors.append("Quantity must be a non-negative number")

        elif data_type == "pricing":
            if "price" not in data:
                errors.append("Pricing data must include price")
            elif not isinstance(data["price"], (int, float)) or data["price"] < 0:
                errors.append("Price must be a non-negative number")

        elif data_type == "listing":
            required_fields = ["title", "description"]
            for field in required_fields:
                if field not in data or not data[field]:
                    errors.append(f"Listing data must include {field}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    async def _transform_data(
        self, data: Dict[str, Any], source: str, target: str, data_type: str
    ) -> Dict[str, Any]:
        """Transform data for target marketplace format."""
        # Start with a copy of the original data
        transformed = data.copy()

        # Apply marketplace-specific transformations
        transformation_key = f"{source}_to_{target}_{data_type}"

        if transformation_key in self.transformation_rules:
            rules = self.transformation_rules[transformation_key]
            for rule in rules:
                transformed = await self._apply_transformation_rule(transformed, rule)

        # Apply default transformations based on marketplace
        if target == "amazon":
            transformed = await self._transform_for_amazon(transformed, data_type)
        elif target == "ebay":
            transformed = await self._transform_for_ebay(transformed, data_type)
        elif target == "walmart":
            transformed = await self._transform_for_walmart(transformed, data_type)

        return transformed

    async def _check_conflicts(
        self, entity_id: str, marketplace: str, new_data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """Check for conflicts with existing data."""
        # This would typically query the database for existing data
        # For now, we'll simulate conflict detection

        conflicts = []
        has_conflicts = False

        # Simulate checking existing data (in real implementation, this would query the database)
        existing_data = await self._get_existing_data(entity_id, marketplace, data_type)

        if existing_data:
            for field, new_value in new_data.items():
                if field in existing_data and existing_data[field] != new_value:
                    conflict = DataConflict(
                        conflict_id=f"conflict_{entity_id}_{marketplace}_{field}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        entity_id=entity_id,
                        field_name=field,
                        marketplace_values={
                            marketplace: existing_data[field],
                            "new": new_value,
                        },
                        resolution_strategy=ConflictResolutionStrategy.LATEST_WINS,
                    )
                    conflicts.append(conflict)
                    has_conflicts = True

                    # Store conflict for later resolution
                    self.pending_conflicts[conflict.conflict_id] = conflict

        return {
            "has_conflicts": has_conflicts,
            "conflicts": conflicts,
        }

    async def _resolve_conflicts(
        self, conflicts: List[DataConflict], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve conflicts and return updated data."""
        resolved_data = data.copy()

        for conflict in conflicts:
            resolved_value = await self._apply_resolution_strategy(
                conflict, conflict.resolution_strategy
            )
            resolved_data[conflict.field_name] = resolved_value

            # Mark conflict as resolved
            conflict.resolved = True
            conflict.resolved_value = resolved_value
            conflict.resolved_at = datetime.now(timezone.utc)

        return resolved_data

    async def _apply_resolution_strategy(
        self, conflict: DataConflict, strategy: ConflictResolutionStrategy
    ) -> Any:
        """Apply a conflict resolution strategy."""
        if strategy == ConflictResolutionStrategy.LATEST_WINS:
            # Return the newest value (assuming 'new' is the latest)
            return conflict.marketplace_values.get("new")

        elif strategy == ConflictResolutionStrategy.HIGHEST_PRIORITY:
            # Return value from highest priority marketplace
            highest_priority = 0
            best_value = None

            for marketplace, value in conflict.marketplace_values.items():
                if marketplace in self.marketplace_priorities:
                    priority = self.marketplace_priorities[marketplace]
                    if priority > highest_priority:
                        highest_priority = priority
                        best_value = value

            return best_value or conflict.marketplace_values.get("new")

        elif strategy == ConflictResolutionStrategy.MERGE_VALUES:
            # Attempt to merge values (for lists, strings, etc.)
            values = list(conflict.marketplace_values.values())
            if all(isinstance(v, list) for v in values):
                # Merge lists
                merged = []
                for v in values:
                    merged.extend(v)
                return list(set(merged))  # Remove duplicates
            elif all(isinstance(v, str) for v in values):
                # Concatenate strings
                return " | ".join(values)
            else:
                # Default to latest wins for non-mergeable types
                return conflict.marketplace_values.get("new")

        else:
            # Default to latest wins
            return conflict.marketplace_values.get("new")

    async def _perform_sync(
        self, entity_id: str, marketplace: str, data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """Perform the actual synchronization to a marketplace."""
        try:
            # This would integrate with marketplace APIs
            # For now, we'll simulate the sync operation

            logger.info(f"Syncing {data_type} for {entity_id} to {marketplace}")

            # Simulate API call delay
            await asyncio.sleep(0.1)

            # Simulate success (in real implementation, this would call marketplace APIs)
            return {
                "marketplace": marketplace,
                "success": True,
                "entity_id": entity_id,
                "data_type": data_type,
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }

        except Exception as e:
            logger.error(f"Sync failed for {marketplace}: {e}")
            return {
                "marketplace": marketplace,
                "success": False,
                "error": str(e),
            }

    async def _get_existing_data(
        self, entity_id: str, marketplace: str, data_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing data for conflict checking."""
        try:
            # Ensure database is initialized
            await self._ensure_database_initialized()

            async with self.database.get_session() as session:
                if data_type == "inventory":
                    # Query inventory data
                    inventory = (
                        await self.market_repository.get_latest_inventory_status(
                            session, int(entity_id), MarketplaceType(marketplace)
                        )
                    )
                    if inventory:
                        return {
                            "quantity": inventory.quantity_available,
                            "reserved": inventory.quantity_reserved,
                            "inbound": inventory.quantity_inbound,
                        }
                elif data_type == "pricing":
                    # Query pricing data
                    pricing_recs = (
                        await self.market_repository.get_latest_pricing_recommendations(
                            session,
                            product_id=int(entity_id),
                            marketplace=MarketplaceType(marketplace),
                            limit=1,
                        )
                    )
                    if pricing_recs:
                        latest = pricing_recs[0]
                        return {
                            "price": float(latest.recommended_price),
                            "currency": latest.currency,
                        }
                # Add more data types as needed
                return None
        except Exception as e:
            logger.warning(f"Failed to get existing data: {e}")
            return None

    async def _apply_transformation_rule(
        self, data: Dict[str, Any], rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a transformation rule to data."""
        # This would apply specific transformation rules
        # For now, just return the data unchanged
        return data

    async def _transform_for_amazon(
        self, data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """Apply Amazon-specific transformations."""
        transformed = data.copy()

        if data_type == "listing":
            # Amazon-specific listing transformations
            if "title" in transformed:
                # Amazon has title length limits
                transformed["title"] = transformed["title"][:200]

        elif data_type == "pricing":
            # Amazon-specific pricing transformations
            if "price" in transformed:
                # Ensure price format is correct for Amazon
                transformed["price"] = round(float(transformed["price"]), 2)

        return transformed

    async def _transform_for_ebay(
        self, data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """Apply eBay-specific transformations."""
        transformed = data.copy()

        if data_type == "listing":
            # eBay-specific listing transformations
            if "title" in transformed:
                # eBay has different title length limits
                transformed["title"] = transformed["title"][:80]

        elif data_type == "pricing":
            # eBay-specific pricing transformations
            if "price" in transformed:
                transformed["price"] = round(float(transformed["price"]), 2)

        return transformed

    async def _transform_for_walmart(
        self, data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """Apply Walmart-specific transformations."""
        transformed = data.copy()

        if data_type == "listing":
            # Walmart-specific listing transformations
            if "title" in transformed:
                transformed["title"] = transformed["title"][:75]

        elif data_type == "pricing":
            # Walmart-specific pricing transformations
            if "price" in transformed:
                transformed["price"] = round(float(transformed["price"]), 2)

        return transformed
