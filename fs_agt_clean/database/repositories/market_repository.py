"""
Market Repository for FlipSync Database Operations
=================================================

This module provides database operations for market-related data including
pricing recommendations, competitor analysis, inventory status, and market decisions.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fs_agt_clean.core.models.marketplace_models import (
    CompetitorAnalysis,
    InventoryStatus,
    MarketDecision,
    MarketplaceType,
    Price,
    PricingRecommendation,
    ProductIdentifier,
)
from fs_agt_clean.database.models.market_models import (
    CompetitorModel,
    InventoryModel,
    MarketDecisionModel,
    PriceHistoryModel,
    PricingRecommendationModel,
    ProductModel,
)

logger = logging.getLogger(__name__)


class MarketRepository:
    """Repository for market-related database operations."""

    async def create_product(
        self,
        session: AsyncSession,
        product_id: ProductIdentifier,
        title: str,
        marketplace: MarketplaceType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProductModel:
        """Create a new product record."""
        try:
            product_data = {
                "asin": product_id.asin,
                "sku": product_id.sku,
                "upc": product_id.upc,
                "ean": product_id.ean,
                "isbn": product_id.isbn,
                "mpn": product_id.mpn,
                "ebay_item_id": product_id.ebay_item_id,
                "internal_id": product_id.internal_id,
                "title": title,
                "marketplace": marketplace.value,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            stmt = insert(ProductModel).values(**product_data)
            result = await session.execute(stmt)
            await session.commit()

            # Get the created product
            product_id_db = result.inserted_primary_key[0]
            stmt = select(ProductModel).where(ProductModel.id == product_id_db)
            result = await session.execute(stmt)
            product = result.scalar_one()

            logger.info(f"Created product: {product.id}")
            return product

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating product: {e}")
            raise

    async def get_product_by_identifier(
        self, session: AsyncSession, product_id: ProductIdentifier
    ) -> Optional[ProductModel]:
        """Get product by any identifier."""
        try:
            conditions = []

            if product_id.asin:
                conditions.append(ProductModel.asin == product_id.asin)
            if product_id.sku:
                conditions.append(ProductModel.sku == product_id.sku)
            if product_id.upc:
                conditions.append(ProductModel.upc == product_id.upc)
            if product_id.ean:
                conditions.append(ProductModel.ean == product_id.ean)
            if product_id.ebay_item_id:
                conditions.append(ProductModel.ebay_item_id == product_id.ebay_item_id)
            if product_id.internal_id:
                conditions.append(ProductModel.internal_id == product_id.internal_id)

            if not conditions:
                return None

            stmt = select(ProductModel).where(or_(*conditions))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting product by identifier: {e}")
            return None

    async def store_price_history(
        self, session: AsyncSession, product_id: int, price: Price, source: str = "api"
    ) -> PriceHistoryModel:
        """Store price history record."""
        try:
            price_data = {
                "product_id": product_id,
                "price": price.amount,
                "currency": price.currency,
                "marketplace": price.marketplace.value,
                "includes_shipping": price.includes_shipping,
                "includes_tax": price.includes_tax,
                "source": source,
                "recorded_at": price.timestamp,
                "created_at": datetime.now(timezone.utc),
            }

            stmt = insert(PriceHistoryModel).values(**price_data)
            result = await session.execute(stmt)
            await session.commit()

            # Get the created record
            price_id = result.inserted_primary_key[0]
            stmt = select(PriceHistoryModel).where(PriceHistoryModel.id == price_id)
            result = await session.execute(stmt)
            price_record = result.scalar_one()

            logger.info(f"Stored price history: {price_record.id}")
            return price_record

        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing price history: {e}")
            raise

    async def get_price_history(
        self,
        session: AsyncSession,
        product_id: int,
        marketplace: Optional[MarketplaceType] = None,
        days: int = 30,
        limit: int = 100,
    ) -> List[PriceHistoryModel]:
        """Get price history for a product."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=days)

            conditions = [
                PriceHistoryModel.product_id == product_id,
                PriceHistoryModel.recorded_at >= cutoff_date,
            ]

            if marketplace:
                conditions.append(PriceHistoryModel.marketplace == marketplace.value)

            stmt = (
                select(PriceHistoryModel)
                .where(and_(*conditions))
                .order_by(desc(PriceHistoryModel.recorded_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []

    async def store_pricing_recommendation(
        self, session: AsyncSession, recommendation: PricingRecommendation
    ) -> PricingRecommendationModel:
        """Store pricing recommendation."""
        try:
            # First, ensure product exists
            product = await self.get_product_by_identifier(
                session, recommendation.product_id
            )
            if not product:
                # Create product if it doesn't exist
                product = await self.create_product(
                    session,
                    recommendation.product_id,
                    f"Product {recommendation.product_id.asin or recommendation.product_id.sku}",
                    recommendation.current_price.marketplace,
                )

            recommendation_data = {
                "product_id": product.id,
                "current_price": recommendation.current_price.amount,
                "recommended_price": recommendation.recommended_price.amount,
                "currency": recommendation.current_price.currency,
                "marketplace": recommendation.current_price.marketplace.value,
                "price_change_direction": recommendation.price_change_direction.value,
                "confidence_score": recommendation.confidence_score,
                "reasoning": recommendation.reasoning,
                "expected_impact": recommendation.expected_impact,
                "market_conditions": recommendation.market_conditions,
                "recommendation_id": recommendation.recommendation_id,
                "expires_at": recommendation.expires_at,
                "created_at": recommendation.created_at,
            }

            stmt = insert(PricingRecommendationModel).values(**recommendation_data)
            result = await session.execute(stmt)
            await session.commit()

            # Get the created record
            rec_id = result.inserted_primary_key[0]
            stmt = select(PricingRecommendationModel).where(
                PricingRecommendationModel.id == rec_id
            )
            result = await session.execute(stmt)
            rec_record = result.scalar_one()

            logger.info(f"Stored pricing recommendation: {rec_record.id}")
            return rec_record

        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing pricing recommendation: {e}")
            raise

    async def get_latest_pricing_recommendations(
        self,
        session: AsyncSession,
        product_id: Optional[int] = None,
        marketplace: Optional[MarketplaceType] = None,
        limit: int = 10,
    ) -> List[PricingRecommendationModel]:
        """Get latest pricing recommendations."""
        try:
            conditions = []

            if product_id:
                conditions.append(PricingRecommendationModel.product_id == product_id)

            if marketplace:
                conditions.append(
                    PricingRecommendationModel.marketplace == marketplace.value
                )

            # Only get non-expired recommendations
            now = datetime.now(timezone.utc)
            conditions.append(
                or_(
                    PricingRecommendationModel.expires_at.is_(None),
                    PricingRecommendationModel.expires_at > now,
                )
            )

            stmt = (
                select(PricingRecommendationModel)
                .where(and_(*conditions) if conditions else True)
                .order_by(desc(PricingRecommendationModel.created_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting pricing recommendations: {e}")
            return []

    async def store_competitor_data(
        self,
        session: AsyncSession,
        product_id: int,
        competitor_asin: str,
        competitor_price: Price,
        competitor_data: Dict[str, Any],
    ) -> CompetitorModel:
        """Store competitor data."""
        try:
            competitor_record = {
                "product_id": product_id,
                "competitor_asin": competitor_asin,
                "competitor_price": competitor_price.amount,
                "currency": competitor_price.currency,
                "marketplace": competitor_price.marketplace.value,
                "competitor_data": competitor_data,
                "recorded_at": competitor_price.timestamp,
                "created_at": datetime.now(timezone.utc),
            }

            stmt = insert(CompetitorModel).values(**competitor_record)
            result = await session.execute(stmt)
            await session.commit()

            # Get the created record
            comp_id = result.inserted_primary_key[0]
            stmt = select(CompetitorModel).where(CompetitorModel.id == comp_id)
            result = await session.execute(stmt)
            comp_record = result.scalar_one()

            logger.info(f"Stored competitor data: {comp_record.id}")
            return comp_record

        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing competitor data: {e}")
            raise

    async def get_competitor_data(
        self, session: AsyncSession, product_id: int, days: int = 7, limit: int = 50
    ) -> List[CompetitorModel]:
        """Get competitor data for a product."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=days)

            stmt = (
                select(CompetitorModel)
                .where(
                    and_(
                        CompetitorModel.product_id == product_id,
                        CompetitorModel.recorded_at >= cutoff_date,
                    )
                )
                .order_by(desc(CompetitorModel.recorded_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting competitor data: {e}")
            return []

    async def store_inventory_status(
        self, session: AsyncSession, inventory: InventoryStatus
    ) -> InventoryModel:
        """Store inventory status."""
        try:
            # Get or create product
            product = await self.get_product_by_identifier(
                session, inventory.product_id
            )
            if not product:
                product = await self.create_product(
                    session,
                    inventory.product_id,
                    f"Product {inventory.product_id.sku}",
                    inventory.marketplace,
                )

            inventory_data = {
                "product_id": product.id,
                "marketplace": inventory.marketplace.value,
                "quantity_available": inventory.quantity_available,
                "quantity_reserved": inventory.quantity_reserved,
                "quantity_inbound": inventory.quantity_inbound,
                "reorder_point": inventory.reorder_point,
                "max_stock_level": inventory.max_stock_level,
                "warehouse_locations": inventory.warehouse_locations,
                "fulfillment_method": inventory.fulfillment_method,
                "last_updated": inventory.last_updated,
                "created_at": datetime.now(timezone.utc),
            }

            stmt = insert(InventoryModel).values(**inventory_data)
            result = await session.execute(stmt)
            await session.commit()

            # Get the created record
            inv_id = result.inserted_primary_key[0]
            stmt = select(InventoryModel).where(InventoryModel.id == inv_id)
            result = await session.execute(stmt)
            inv_record = result.scalar_one()

            logger.info(f"Stored inventory status: {inv_record.id}")
            return inv_record

        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing inventory status: {e}")
            raise

    async def get_latest_inventory_status(
        self,
        session: AsyncSession,
        product_id: int,
        marketplace: Optional[MarketplaceType] = None,
    ) -> Optional[InventoryModel]:
        """Get latest inventory status for a product."""
        try:
            conditions = [InventoryModel.product_id == product_id]

            if marketplace:
                conditions.append(InventoryModel.marketplace == marketplace.value)

            stmt = (
                select(InventoryModel)
                .where(and_(*conditions))
                .order_by(desc(InventoryModel.last_updated))
                .limit(1)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting inventory status: {e}")
            return None

    async def store_market_decision(
        self, session: AsyncSession, decision: MarketDecision
    ) -> MarketDecisionModel:
        """Store market decision."""
        try:
            # Get or create product
            product = await self.get_product_by_identifier(session, decision.product_id)
            if not product:
                product = await self.create_product(
                    session,
                    decision.product_id,
                    f"Product {decision.product_id.asin or decision.product_id.sku}",
                    MarketplaceType.AMAZON,  # Default marketplace
                )

            decision_data = {
                "decision_id": decision.decision_id,
                "decision_type": decision.decision_type,
                "product_id": product.id,
                "current_state": decision.current_state,
                "recommended_action": decision.recommended_action,
                "reasoning": decision.reasoning,
                "confidence_score": decision.confidence_score,
                "expected_outcome": decision.expected_outcome,
                "risk_assessment": decision.risk_assessment,
                "requires_approval": decision.requires_approval,
                "auto_execute": decision.auto_execute,
                "approved_by": decision.approved_by,
                "created_at": decision.created_at,
                "approved_at": decision.approved_at,
                "executed_at": decision.executed_at,
            }

            stmt = insert(MarketDecisionModel).values(**decision_data)
            result = await session.execute(stmt)
            await session.commit()

            # Get the created record
            dec_id = result.inserted_primary_key[0]
            stmt = select(MarketDecisionModel).where(MarketDecisionModel.id == dec_id)
            result = await session.execute(stmt)
            dec_record = result.scalar_one()

            logger.info(f"Stored market decision: {dec_record.id}")
            return dec_record

        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing market decision: {e}")
            raise

    async def get_market_decisions(
        self,
        session: AsyncSession,
        product_id: Optional[int] = None,
        decision_type: Optional[str] = None,
        requires_approval: Optional[bool] = None,
        limit: int = 20,
    ) -> List[MarketDecisionModel]:
        """Get market decisions with filters."""
        try:
            conditions = []

            if product_id:
                conditions.append(MarketDecisionModel.product_id == product_id)

            if decision_type:
                conditions.append(MarketDecisionModel.decision_type == decision_type)

            if requires_approval is not None:
                conditions.append(
                    MarketDecisionModel.requires_approval == requires_approval
                )

            stmt = (
                select(MarketDecisionModel)
                .where(and_(*conditions) if conditions else True)
                .order_by(desc(MarketDecisionModel.created_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting market decisions: {e}")
            return []
