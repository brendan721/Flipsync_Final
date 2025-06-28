import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fs_agt_clean.agents.base.base import BaseUnifiedAgent
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.core.monitoring.alerts.models import Alert, AlertSeverity, AlertType
from fs_agt_clean.core.utils.config import get_settings
from fs_agt_clean.services.logistics.shipping_service import ShippingService

logger: logging.Logger = logging.getLogger(__name__)


class ShippingUnifiedAgent(BaseUnifiedAgent):
    """UnifiedAgent for managing shipping operations."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
    ):
        """Initialize shipping agent."""
        if agent_id is None:
            agent_id = "shipping_agent"
        if config_manager is None:
            config_manager = ConfigManager()
        if alert_manager is None:
            alert_manager = AlertManager()

        super().__init__(agent_id, config_manager, alert_manager)
        self.shipping_service = ShippingService()
        self.settings = get_settings()

    async def _process_event(self, event: dict) -> None:
        """Process a shipping event."""
        try:
            result = await self.process_task(event)
            await self.store_experience(
                {
                    "event": event,
                    "result": result,
                    "success": result.get("success", False),
                }
            )
        except Exception as e:
            logger.error("Error processing shipping event: %s", str(e))
            alert = Alert(
                alert_id=f"shipping_{self.agent_id}_{event.get('operation', 'unknown')}",
                alert_type=AlertType.CUSTOM,
                message=f"Failed to process event: {str(e)}",
                severity=AlertSeverity.HIGH,
                metric_type="counter",
                metric_value=1,
                threshold=0,
                timestamp=datetime.now(timezone.utc),
            )
            await self.alert_manager.process_alert(alert)
            raise

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process shipping-related tasks.

        Args:
            task: Task details containing operation and parameters

        Returns:
            Task result
        """
        operation = task.get("operation")
        params = task.get("parameters", {})
        try:
            if operation == "calculate_rates":
                return await self._handle_rate_calculation(params)
            elif operation == "create_label":
                return await self._handle_label_creation(params)
            elif operation == "track_shipment":
                return await self._handle_tracking(params)
            elif operation == "validate_address":
                return await self._handle_address_validation(params)
            elif operation == "process_refund":
                return await self._handle_refund(params)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        except Exception as e:
            logger.error("Error processing shipping task: %s", str(e))
            alert = Alert(
                alert_id=f"shipping_task_{self.agent_id}_{operation}",
                alert_type=AlertType.CUSTOM,
                message=f"Failed to process {operation}: {str(e)}",
                severity=AlertSeverity.HIGH,
                metric_type="counter",
                metric_value=1,
                threshold=0,
                timestamp=datetime.now(timezone.utc),
            )
            await self.alert_manager.process_alert(alert)
            return {"success": False, "error": str(e)}

    async def _handle_rate_calculation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipping rate calculation."""
        try:
            rates = await self.shipping_service.calculate_rates(
                from_address=params["from_address"],
                to_address=params["to_address"],
                parcel=params["parcel"],
                carrier_accounts=params.get("carrier_accounts"),
                is_return=params.get("is_return", False),
            )
            return {"success": True, "rates": rates}
        except Exception as e:
            logger.error("Rate calculation failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _handle_label_creation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipping label creation."""
        try:
            label = await self.shipping_service.create_label(
                rate_id=params["rate_id"], is_test=params.get("is_test", False)
            )
            if not label:
                return {"success": False, "error": "Failed to create label"}
            return {"success": True, "label": label}
        except Exception as e:
            logger.error("Label creation failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _handle_tracking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipment tracking."""
        try:
            tracking_info = await self.shipping_service.track_shipment(
                tracking_number=params["tracking_number"], carrier=params["carrier"]
            )
            if not tracking_info:
                return {"success": False, "error": "Failed to get tracking information"}
            return {"success": True, "tracking": tracking_info}
        except Exception as e:
            logger.error("Tracking lookup failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _handle_address_validation(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle address validation."""
        try:
            validated_address = await self.shipping_service.validate_address(
                address=params["address"]
            )
            if not validated_address:
                return {"success": False, "error": "Address validation failed"}
            return {"success": True, "address": validated_address}
        except Exception as e:
            logger.error("Address validation failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _handle_refund(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipping label refund."""
        try:
            refund_info = await self.shipping_service.get_refund(
                transaction_id=params["transaction_id"]
            )
            if not refund_info:
                return {"success": False, "error": "Failed to process refund"}
            return {"success": True, "refund": refund_info}
        except Exception as e:
            logger.error("Refund processing failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def communicate(self, target_agent: str, message: Dict[str, Any]):
        """Send message to another agent."""
        try:
            pass
        except Exception as e:
            logger.error("Communication failed: %s", str(e))

    async def shutdown(self):
        """Clean shutdown of the agent."""
        try:
            pass
        except Exception as e:
            logger.error("Shutdown failed: %s", str(e))

    async def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process incoming message.

        Args:
            message: Message to process
        """
        await self._process_event(message)

    async def take_action(self, action: Dict[str, Any]) -> None:
        """
        Take a specific action.

        Args:
            action: Action dictionary containing action type and parameters
        """
        await self.process_task(action)

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status.

        Returns:
            UnifiedAgent status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": "ShippingUnifiedAgent",
            "status": "operational",
            "last_activity": datetime.now().isoformat(),
        }
