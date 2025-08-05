from typing import Any, Dict, Optional
import logging
from datetime import datetime, timezone

from fs_agt_clean.agents.market.base_market_agent import BaseMarketAutonomousAgent
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

logger = logging.getLogger(__name__)


class InventoryAutonomousAgent(BaseMarketAutonomousAgent):

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
    ):
        # Provide defaults if not provided
        if agent_id is None:
            agent_id = "inventory_agent"
        if config is None:
            config = {}
        if config_manager is None:
            config_manager = ConfigManager()
        if alert_manager is None:
            alert_manager = AlertManager()
        if battery_optimizer is None:
            battery_optimizer = BatteryOptimizer()

        super().__init__(
            agent_id=agent_id,
            marketplace="inventory",
            config_manager=config_manager,
            alert_manager=alert_manager,
            battery_optimizer=battery_optimizer,
            config=config,
        )
        self.inventory_cache: Dict[str, Dict[str, Any]] = {}
        self.metrics.update({"inventory_updates": 0, "stock_alerts": 0})

    async def update_metrics(self, metric_name: str, value: int = 1) -> None:
        """Update metrics for the agent."""
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
        else:
            self.metrics[metric_name] = value

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process inventory tasks"""
        task_type = task.get("type")
        if task_type == "update":
            return await self._handle_inventory_update(task)
        elif task_type == "check":
            return await self._handle_inventory_check(task)
        return {"success": False, "error": "Unknown task type"}

    async def _handle_listing_event(self, event: Dict[str, Any]) -> None:
        """Handle inventory-related listing events"""
        event_type = event.get("type")
        if event_type == "stock_update":
            await self._process_stock_update(event)

    async def _process_inventory_updates(self) -> None:
        """Process pending inventory updates."""
        await self.update_metrics("inventory_updates")

    async def _check_stock_levels(self) -> None:
        """Check stock levels and generate alerts."""
        await self.update_metrics("stock_alerts")

    async def _sync_inventory(self) -> None:
        """Sync inventory across marketplaces."""
        await self.update_metrics("sync_operations")

    async def _handle_stock_update(self, event: Dict[str, Any]) -> None:
        """Handle stock update events."""
        sku = event.get("sku")
        if sku:
            self.inventory_cache[sku] = event.get("data", {})
            await self.update_metrics("inventory_updates")

    async def _handle_inventory_sync(self, event: Dict[str, Any]) -> None:
        """Handle inventory sync events."""
        marketplace = event.get("marketplace")
        if marketplace:
            await self.update_metrics("sync_operations")

    async def get_stock_level(self, sku: str) -> Optional[int]:
        """Get current stock level for a SKU."""
        return self.inventory_cache.get(sku, {}).get("stock_level")

    async def update_stock_level(self, sku: str, quantity: int) -> None:
        """Update stock level for a SKU."""
        if sku not in self.inventory_cache:
            self.inventory_cache[sku] = {}
        self.inventory_cache[sku]["stock_level"] = quantity
        await self.update_metrics("inventory_updates")

    async def execute_command(
        self, command: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute commands sent to the inventory agent."""
        try:
            logger.info(f"🎯 InventoryAgent executing command: {command}")

            if command == "process_marketplace_inventory":
                return await self._handle_process_marketplace_inventory(parameters)
            elif command == "get_inventory_status":
                return await self._handle_get_inventory_status(parameters)
            else:
                logger.warning(f"Unknown command: {command}")
                return {"success": False, "error": f"Unknown command: {command}"}

        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_process_marketplace_inventory(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the process_marketplace_inventory command."""
        try:
            user_id = parameters.get("user_id")
            marketplace = parameters.get("marketplace")
            inventory_data = parameters.get("inventory_data", [])
            source = parameters.get("source")

            logger.info(
                f"📦 Processing {len(inventory_data)} inventory items from {marketplace} for user {user_id}"
            )

            if not user_id or not marketplace or not inventory_data:
                return {"success": False, "error": "Missing required parameters"}

            # Convert eBay inventory data to our database format
            processed_items = []
            for item in inventory_data:
                processed_item = await self._convert_ebay_item_to_db_format(
                    item, user_id
                )
                if processed_item:
                    processed_items.append(processed_item)

            logger.info(f"📝 Converted {len(processed_items)} items to database format")

            # Store items in database using inventory repository
            stored_items = await self._store_inventory_items(processed_items)

            logger.info(
                f"💾 Successfully stored {len(stored_items)} inventory items in database"
            )

            return {
                "success": True,
                "items_processed": len(inventory_data),
                "items_stored": len(stored_items),
                "user_id": user_id,
                "marketplace": marketplace,
                "source": source,
            }

        except Exception as e:
            logger.error(f"Error processing marketplace inventory: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_get_inventory_status(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the get_inventory_status command."""
        try:
            user_id = parameters.get("user_id")
            marketplace = parameters.get("marketplace")

            # For now, return basic status from cache
            cache_items = len(
                [k for k in self.inventory_cache.keys() if k.startswith(f"{user_id}:")]
            )

            return {
                "success": True,
                "user_id": user_id,
                "marketplace": marketplace,
                "cached_items": cache_items,
                "status": "active",
            }

        except Exception as e:
            logger.error(f"Error getting inventory status: {e}")
            return {"success": False, "error": str(e)}

    async def _convert_ebay_item_to_db_format(
        self, ebay_item: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Convert eBay inventory item to database format."""
        try:
            sku = ebay_item.get("sku")
            if not sku:
                logger.warning("Skipping eBay item without SKU")
                return None

            # Extract basic item information
            product = ebay_item.get("product", {})
            availability = ebay_item.get("availability", {})
            condition = ebay_item.get("condition", "USED")

            # Extract quantity from availability
            ship_to_location = availability.get("shipToLocationAvailability", {})
            quantity = ship_to_location.get("quantity", 0)

            # Extract product details
            title = product.get("title", f"eBay Item {sku}")
            description = product.get("description", "")
            brand = product.get("brand", "")
            mpn = product.get("mpn", "")

            # Extract aspects/item specifics
            aspects = product.get("aspects", {})

            # Build metadata JSON with eBay-specific information
            metadata = {
                "ebay_data": ebay_item,
                "condition": condition,
                "brand": brand,
                "mpn": mpn,
                "aspects": aspects,
                "availability": availability,
                "user_id": user_id,
                "import_timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Convert to our database format
            db_item = {
                "sku": sku,
                "name": title[:255],  # Truncate to fit database field
                "description": description,
                "quantity": int(quantity) if quantity else 0,
                "condition_ebay": condition,
                "marketplace_source": "eBay",
                "metadata_json": metadata,
                "last_sync_at": datetime.now(timezone.utc),
                "is_active": True,
                "created_by": user_id,
                "updated_by": user_id,
            }

            logger.debug(f"Converted eBay item {sku} to database format")
            return db_item

        except Exception as e:
            logger.error(f"Error converting eBay item to database format: {e}")
            return None

    async def _store_inventory_items(self, items_data: list) -> list:
        """Store inventory items in the database using the inventory repository."""
        try:
            # Import the inventory repository and database session
            from fs_agt_clean.core.db.database import get_db
            from fs_agt_clean.database.repositories.inventory_repository import (
                InventoryRepository,
            )

            # Get database session
            async for db_session in get_db():
                try:
                    # Create inventory repository instance
                    inventory_repo = InventoryRepository(db_session)

                    # Use the upsert method to store items
                    stored_items = await inventory_repo.upsert_ebay_inventory_items(
                        items_data
                    )

                    logger.info(
                        f"Successfully stored {len(stored_items)} items in database"
                    )
                    return stored_items

                except Exception as e:
                    logger.error(f"Error storing items in database: {e}")
                    await db_session.rollback()
                    raise
                finally:
                    await db_session.close()

        except Exception as e:
            logger.error(f"Error in _store_inventory_items: {e}")
            return []
