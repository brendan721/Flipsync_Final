"""
Revenue Repository for FlipSync Database Operations
==================================================

Repository pattern implementation for revenue-related database operations
including shipping arbitrage, revenue tracking, and user rewards management.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fs_agt_clean.database.models.revenue import (
    RevenueOptimizationLog,
    RevenueTracking,
    ShippingArbitrageCalculation,
    UnifiedUserRewardsBalance,
)
from fs_agt_clean.database.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RevenueRepository(BaseRepository):
    """Repository for revenue-related database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize revenue repository."""
        super().__init__(session)
        self.session = session

    # Shipping Arbitrage Operations
    async def create_shipping_calculation(
        self, calculation_data: Dict[str, Any]
    ) -> ShippingArbitrageCalculation:
        """Create a new shipping arbitrage calculation record."""
        try:
            calculation = ShippingArbitrageCalculation(**calculation_data)
            self.session.add(calculation)
            await self.session.commit()
            await self.session.refresh(calculation)

            logger.info(f"Created shipping calculation: {calculation.calculation_id}")
            return calculation

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating shipping calculation: {e}")
            raise

    async def get_shipping_calculations_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[ShippingArbitrageCalculation]:
        """Get shipping calculations for a user."""
        try:
            query = (
                select(ShippingArbitrageCalculation)
                .where(ShippingArbitrageCalculation.user_id == user_id)
                .order_by(desc(ShippingArbitrageCalculation.created_at))
                .limit(limit)
                .offset(offset)
            )

            result = await self.session.execute(query)
            calculations = result.scalars().all()

            logger.info(
                f"Retrieved {len(calculations)} shipping calculations for user {user_id}"
            )
            return list(calculations)

        except Exception as e:
            logger.error(f"Error retrieving shipping calculations: {e}")
            raise

    async def get_total_savings_by_user(self, user_id: str) -> Decimal:
        """Get total shipping savings for a user."""
        try:
            query = select(func.sum(ShippingArbitrageCalculation.savings_amount)).where(
                ShippingArbitrageCalculation.user_id == user_id
            )

            result = await self.session.execute(query)
            total_savings = result.scalar() or Decimal("0.00")

            logger.info(f"Total savings for user {user_id}: {total_savings}")
            return total_savings

        except Exception as e:
            logger.error(f"Error calculating total savings: {e}")
            raise

    # Revenue Tracking Operations
    async def create_revenue_record(
        self, revenue_data: Dict[str, Any]
    ) -> RevenueTracking:
        """Create a new revenue tracking record."""
        try:
            revenue = RevenueTracking(**revenue_data)
            self.session.add(revenue)
            await self.session.commit()
            await self.session.refresh(revenue)

            logger.info(f"Created revenue record: {revenue.revenue_id}")
            return revenue

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating revenue record: {e}")
            raise

    async def get_revenue_by_user(
        self,
        user_id: str,
        revenue_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RevenueTracking]:
        """Get revenue records for a user."""
        try:
            query = select(RevenueTracking).where(RevenueTracking.user_id == user_id)

            if revenue_type:
                query = query.where(RevenueTracking.revenue_type == revenue_type)

            query = (
                query.order_by(desc(RevenueTracking.created_at))
                .limit(limit)
                .offset(offset)
            )

            result = await self.session.execute(query)
            revenue_records = result.scalars().all()

            logger.info(
                f"Retrieved {len(revenue_records)} revenue records for user {user_id}"
            )
            return list(revenue_records)

        except Exception as e:
            logger.error(f"Error retrieving revenue records: {e}")
            raise

    async def get_total_revenue_by_user(
        self, user_id: str, revenue_type: Optional[str] = None
    ) -> Decimal:
        """Get total revenue for a user."""
        try:
            query = select(func.sum(RevenueTracking.amount)).where(
                RevenueTracking.user_id == user_id
            )

            if revenue_type:
                query = query.where(RevenueTracking.revenue_type == revenue_type)

            result = await self.session.execute(query)
            total_revenue = result.scalar() or Decimal("0.00")

            logger.info(f"Total revenue for user {user_id}: {total_revenue}")
            return total_revenue

        except Exception as e:
            logger.error(f"Error calculating total revenue: {e}")
            raise

    # UnifiedUser Rewards Operations
    async def get_user_rewards_balance(
        self, user_id: str
    ) -> Optional[UnifiedUserRewardsBalance]:
        """Get user rewards balance."""
        try:
            query = select(UnifiedUserRewardsBalance).where(
                UnifiedUserRewardsBalance.user_id == user_id
            )
            result = await self.session.execute(query)
            balance = result.scalar_one_or_none()

            if balance:
                logger.info(
                    f"Retrieved rewards balance for user {user_id}: {balance.current_balance}"
                )
            else:
                logger.info(f"No rewards balance found for user {user_id}")

            return balance

        except Exception as e:
            logger.error(f"Error retrieving user rewards balance: {e}")
            raise

    async def create_or_update_rewards_balance(
        self, user_id: str, balance_data: Dict[str, Any]
    ) -> UnifiedUserRewardsBalance:
        """Create or update user rewards balance."""
        try:
            # Check if balance exists
            existing_balance = await self.get_user_rewards_balance(user_id)

            if existing_balance:
                # Update existing balance
                for key, value in balance_data.items():
                    if hasattr(existing_balance, key):
                        setattr(existing_balance, key, value)

                existing_balance.updated_at = datetime.now(timezone.utc)
                await self.session.commit()
                await self.session.refresh(existing_balance)

                logger.info(f"Updated rewards balance for user {user_id}")
                return existing_balance
            else:
                # Create new balance
                balance_data["user_id"] = user_id
                new_balance = UnifiedUserRewardsBalance(**balance_data)
                self.session.add(new_balance)
                await self.session.commit()
                await self.session.refresh(new_balance)

                logger.info(f"Created rewards balance for user {user_id}")
                return new_balance

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating/updating rewards balance: {e}")
            raise

    async def add_rewards_earning(
        self, user_id: str, amount: Decimal, source: str
    ) -> UnifiedUserRewardsBalance:
        """Add rewards earning to user balance."""
        try:
            balance = await self.get_user_rewards_balance(user_id)

            if not balance:
                # Create new balance if doesn't exist
                balance = await self.create_or_update_rewards_balance(
                    user_id,
                    {
                        "current_balance": amount,
                        "lifetime_earned": amount,
                        "earning_history": [
                            {
                                "amount": float(amount),
                                "source": source,
                                "date": datetime.now(timezone.utc).isoformat(),
                            }
                        ],
                    },
                )
            else:
                # Update existing balance
                balance.current_balance += amount
                balance.lifetime_earned += amount
                balance.last_earning_date = datetime.now(timezone.utc)

                # Update earning history
                earning_record = {
                    "amount": float(amount),
                    "source": source,
                    "date": datetime.now(timezone.utc).isoformat(),
                }

                if balance.earning_history:
                    balance.earning_history.append(earning_record)
                else:
                    balance.earning_history = [earning_record]

                await self.session.commit()
                await self.session.refresh(balance)

            logger.info(f"Added {amount} rewards to user {user_id} from {source}")
            return balance

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding rewards earning: {e}")
            raise

    # Revenue Optimization Logs
    async def create_optimization_log(
        self, log_data: Dict[str, Any]
    ) -> RevenueOptimizationLog:
        """Create a revenue optimization log entry."""
        try:
            log_entry = RevenueOptimizationLog(**log_data)
            self.session.add(log_entry)
            await self.session.commit()
            await self.session.refresh(log_entry)

            logger.info(f"Created optimization log: {log_entry.log_id}")
            return log_entry

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating optimization log: {e}")
            raise

    async def get_optimization_logs_by_user(
        self,
        user_id: str,
        optimization_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RevenueOptimizationLog]:
        """Get optimization logs for a user."""
        try:
            query = select(RevenueOptimizationLog).where(
                RevenueOptimizationLog.user_id == user_id
            )

            if optimization_type:
                query = query.where(
                    RevenueOptimizationLog.optimization_type == optimization_type
                )

            query = (
                query.order_by(desc(RevenueOptimizationLog.created_at))
                .limit(limit)
                .offset(offset)
            )

            result = await self.session.execute(query)
            logs = result.scalars().all()

            logger.info(f"Retrieved {len(logs)} optimization logs for user {user_id}")
            return list(logs)

        except Exception as e:
            logger.error(f"Error retrieving optimization logs: {e}")
            raise


# Export repository
__all__ = ["RevenueRepository"]
