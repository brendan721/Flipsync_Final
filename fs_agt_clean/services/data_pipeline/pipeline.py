import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from uuid import uuid4

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.data_pipeline.acquisition_agent import DataAcquisitionUnifiedAgent
from fs_agt_clean.core.services.communication import EventType
from fs_agt_clean.core.services.communication.event_bus import Event, EventBus
from fs_agt_clean.core.utils.token_manager import TokenManager
from fs_agt_clean.services.data_pipeline.models import (
    ProductData,
    TransformationResult,
    ValidationResult,
)
from fs_agt_clean.services.data_pipeline.validators import DataValidator

"\nMain data pipeline implementation.\n"
logger = logging.getLogger(__name__)


class DataPipeline:
    """Main pipeline for data processing and transformation."""

    def __init__(
        self,
        event_bus: EventBus,
        config_manager: ConfigManager,
        log_manager: Any,
        data_cache: Any,
        amazon_service: Any,
        openai_service: Any,
        market_analyzer: Any,
    ):
        """Initialize the data pipeline.

        Args:
            event_bus: Event bus instance for publishing events
            config_manager: Config manager for accessing configuration
            log_manager: Log manager instance
            data_cache: Data cache instance
            amazon_service: Amazon service instance
            openai_service: OpenAI service instance
            market_analyzer: Market analyzer instance
        """
        self.event_bus = event_bus
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.data_cache = data_cache
        self.amazon_service = amazon_service
        self.openai_service = openai_service
        self.market_analyzer = market_analyzer
        self.validator = DataValidator()
        self.transformers: List[Callable[[ProductData], Dict[str, Any]]] = []
        self.logger = logging.getLogger(__name__)

    def add_transformer(
        self, transformer: Callable[[ProductData], Dict[str, Any]]
    ) -> None:
        """Add a transformer function to the pipeline.

        Args:
            transformer: Function that takes ProductData and returns Dict[str, Any]
        """
        self.transformers.append(transformer)
        self.logger.debug("Added transformer %s", transformer.__name__)

    async def process_sheet_data(self, sheet_data: List[Dict[str, Any]]) -> None:
        """Process data from Google Sheets"""
        try:
            for item in sheet_data:
                try:
                    asin = item.get("asin", "")
                    if not asin:
                        self.logger.error("Missing ASIN in sheet data")
                        continue

                    # Acquire data using Amazon service
                    try:
                        product_data = await self.amazon_service.get_product_data(asin)
                        if not product_data:
                            continue
                    except Exception as e:
                        await self.event_bus.publish(
                            Event(
                                type=EventType.PROCESSING_ERROR,
                                data={"error": str(e), "item": item},
                                source="data_pipeline",
                            )
                        )
                        continue

                    # Create ProductData instance
                    product = ProductData(**product_data)

                    # Validate the data
                    validation_result = await self.validator.validate_product(product)
                    if not validation_result.is_valid:
                        await self.event_bus.publish(
                            Event(
                                type=EventType.VALIDATION_ERROR,
                                data={"errors": validation_result.errors, "item": item},
                                source="data_pipeline",
                            )
                        )
                        continue

                    # Transform the data
                    transformed_data = self._transform_and_store(product)

                    # Publish success event
                    await self.event_bus.publish(
                        Event(
                            type=EventType.DATA_PROCESSED,
                            data={"product": transformed_data},
                            source="data_pipeline",
                        )
                    )

                except Exception as e:
                    self.logger.error("Error processing sheet item: %s", str(e))
                    await self.event_bus.publish(
                        Event(
                            type=EventType.PROCESSING_ERROR,
                            data={"error": str(e), "item": item},
                            source="data_pipeline",
                        )
                    )

        except Exception as e:
            self.logger.error("Error processing sheet data: %s", str(e))
            await self.event_bus.publish(
                Event(
                    type=EventType.PROCESSING_ERROR,
                    data={"error": str(e)},
                    source="data_pipeline",
                )
            )

    async def process_amazon_data(self, asins: List[str]) -> List[TransformationResult]:
        """Process Amazon product data."""
        results = []
        for asin in asins:
            try:
                data = await self.amazon_service.get_product_data(asin)
                product = ProductData(**data)
                validation = await self.validator.validate_product(product)

                if validation.is_valid:
                    results.append(
                        TransformationResult(
                            success=True,
                            transformed_data=product,
                            error_message=None,
                            original_data=data,
                            transformation_type="amazon_data",
                        )
                    )
                else:
                    await self.event_bus.publish(
                        Event(
                            type=EventType.VALIDATION_ERROR,
                            data={"errors": validation.errors, "product_id": asin},
                            source="data_pipeline",
                        )
                    )
                    results.append(
                        TransformationResult(
                            success=False,
                            transformed_data=None,
                            error_message=f"Validation failed: {validation.errors}",
                            original_data=data,
                            transformation_type="amazon_data",
                        )
                    )
            except Exception as e:
                await self.event_bus.publish(
                    Event(
                        type=EventType.PROCESSING_ERROR,
                        data={"error": str(e), "product_id": asin},
                        source="data_pipeline",
                    )
                )
                results.append(
                    TransformationResult(
                        success=False,
                        transformed_data=None,
                        error_message=str(e),
                        original_data={},
                        transformation_type="amazon_data",
                    )
                )
        return results

    def _transform_and_store(self, product: ProductData) -> Dict[str, Any]:
        """Apply all transformers to the product data and store results.

        Args:
            product: The product data to transform

        Returns:
            Dict containing all transformed data
        """
        transformed_data = {}
        for transformer in self.transformers:
            try:
                result = transformer(product)
                transformed_data.update(result)
            except Exception as e:
                self.logger.error(
                    "Transformer %s failed: %s", transformer.__name__, str(e)
                )

                continue

        # Store in cache if available
        if self.data_cache:
            try:
                self.data_cache.store(product.asin, transformed_data)
            except Exception as e:
                self.logger.error("Failed to store in cache: %s", str(e))

        return transformed_data

    async def shutdown(self) -> None:
        """Shutdown the pipeline and clean up resources."""
        self.transformers.clear()
        await self.event_bus.publish(
            Event(
                type=EventType.PIPELINE_SHUTDOWN,
                data={"status": "completed"},
                source="data_pipeline",
            )
        )
