"""
Best Offer Management Service for FlipSync
==========================================

This service provides automated Best Offer management with user-configurable thresholds:
- Profit vs speed slider implementation
- Automated offer acceptance based on user preferences
- Time-based pricing strategies
- Integration with eBay Best Offer API
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.monitoring.cost_tracker import record_ai_cost, CostCategory
from fs_agt_clean.database.repositories.marketplace_repository import MarketplaceRepository

logger = logging.getLogger(__name__)


class OfferAction(str, Enum):
    """Possible actions for incoming offers."""
    ACCEPT = "accept"
    DECLINE = "decline"
    COUNTER = "counter"
    IGNORE = "ignore"


class ProfitSpeedPreference(str, Enum):
    """Profit vs speed preference levels."""
    MAX_SPEED = "max_speed"      # 0.0 - Accept lower offers for faster sales
    BALANCED = "balanced"        # 0.5 - Balanced approach
    MAX_PROFIT = "max_profit"    # 1.0 - Hold out for higher offers


@dataclass
class BestOfferSettings:
    """UnifiedUser-configurable Best Offer settings."""
    
    # Core preferences
    profit_vs_speed_preference: float  # 0.0 = max speed, 1.0 = max profit
    minimum_profit_margin: float      # Minimum acceptable profit percentage (e.g., 0.15 = 15%)
    maximum_discount_percentage: float # Maximum discount from listing price (e.g., 0.30 = 30%)
    
    # Advanced settings
    auto_accept_enabled: bool = True
    auto_counter_enabled: bool = True
    time_decay_enabled: bool = True
    
    # Time-based rules
    initial_acceptance_threshold: float = 0.90  # Accept offers >= 90% of listing price initially
    time_decay_days: int = 7                    # Days before reducing threshold
    final_acceptance_threshold: float = 0.70    # Final threshold after time decay
    
    # Inventory-based rules
    high_inventory_threshold: int = 10          # Consider high inventory if > 10 units
    high_inventory_discount_bonus: float = 0.05 # Additional 5% discount for high inventory


@dataclass
class eBayOffer:
    """eBay Best Offer data structure."""
    
    offer_id: str
    listing_id: str
    buyer_id: str
    offer_amount: float
    listing_price: float
    offer_timestamp: datetime
    message: Optional[str] = None
    buyer_feedback_score: int = 0
    buyer_feedback_percentage: float = 100.0


@dataclass
class OfferResponse:
    """Response to an eBay offer."""
    
    action: OfferAction
    counter_amount: Optional[float] = None
    message: Optional[str] = None
    reasoning: str = ""
    confidence: float = 0.0


@dataclass
class ListingData:
    """Listing data for offer evaluation."""
    
    listing_id: str
    listing_price: float
    cost_basis: float
    current_inventory: int
    days_listed: int
    view_count: int
    watcher_count: int
    category: str
    condition: str


class BestOfferManager:
    """Automated Best Offer management with user-configurable thresholds."""
    
    def __init__(self, marketplace_repository: Optional[MarketplaceRepository] = None):
        self.marketplace_repository = marketplace_repository or MarketplaceRepository()
        self.active_settings: Dict[str, BestOfferSettings] = {}  # user_id -> settings
        
    async def configure_user_settings(self, user_id: str, settings: BestOfferSettings) -> bool:
        """Configure Best Offer settings for a user."""
        try:
            # Validate settings
            if not self._validate_settings(settings):
                return False
            
            # Store settings
            self.active_settings[user_id] = settings
            
            # Persist to database
            await self.marketplace_repository.save_best_offer_settings(user_id, settings)
            
            logger.info(f"Best Offer settings configured for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring Best Offer settings: {e}")
            return False
    
    async def process_incoming_offer(
        self, 
        offer: eBayOffer, 
        listing_data: ListingData,
        user_id: str
    ) -> OfferResponse:
        """Process incoming offer based on user settings."""
        
        try:
            # Get user settings
            settings = await self._get_user_settings(user_id)
            if not settings:
                return OfferResponse(
                    action=OfferAction.IGNORE,
                    reasoning="No Best Offer settings configured for user"
                )
            
            # Calculate acceptance threshold
            acceptance_threshold = await self._calculate_acceptance_threshold(
                settings, listing_data, offer
            )
            
            # Calculate offer percentage
            offer_percentage = offer.offer_amount / offer.listing_price
            
            # Determine action
            if offer_percentage >= acceptance_threshold:
                return OfferResponse(
                    action=OfferAction.ACCEPT,
                    reasoning=f"Offer {offer_percentage:.1%} meets threshold {acceptance_threshold:.1%}",
                    confidence=0.9
                )
            
            elif settings.auto_counter_enabled and offer_percentage >= 0.70:
                # Counter with optimal price
                counter_amount = await self._calculate_counter_offer(
                    settings, listing_data, offer, acceptance_threshold
                )
                
                return OfferResponse(
                    action=OfferAction.COUNTER,
                    counter_amount=counter_amount,
                    reasoning=f"Counter offer at {counter_amount:.2f} (threshold: {acceptance_threshold:.1%})",
                    confidence=0.8
                )
            
            else:
                return OfferResponse(
                    action=OfferAction.DECLINE,
                    reasoning=f"Offer {offer_percentage:.1%} below minimum threshold",
                    confidence=0.7
                )
                
        except Exception as e:
            logger.error(f"Error processing offer: {e}")
            return OfferResponse(
                action=OfferAction.IGNORE,
                reasoning=f"Error processing offer: {str(e)}"
            )
    
    async def _calculate_acceptance_threshold(
        self, 
        settings: BestOfferSettings, 
        listing_data: ListingData,
        offer: eBayOffer
    ) -> float:
        """Calculate dynamic acceptance threshold based on multiple factors."""
        
        # Start with base threshold from profit vs speed preference
        base_threshold = self._calculate_base_threshold(settings)
        
        # Apply time decay if enabled
        if settings.time_decay_enabled:
            time_factor = self._calculate_time_decay_factor(settings, listing_data.days_listed)
            base_threshold *= time_factor
        
        # Apply inventory factor
        inventory_factor = self._calculate_inventory_factor(settings, listing_data.current_inventory)
        base_threshold *= inventory_factor
        
        # Apply performance factor (views, watchers)
        performance_factor = self._calculate_performance_factor(listing_data)
        base_threshold *= performance_factor
        
        # Ensure minimum profit margin
        min_threshold_for_profit = (listing_data.cost_basis * (1 + settings.minimum_profit_margin)) / listing_data.listing_price
        
        # Take the higher of calculated threshold and minimum profit threshold
        final_threshold = max(base_threshold, min_threshold_for_profit)
        
        # Ensure within maximum discount bounds
        max_discount_threshold = 1.0 - settings.maximum_discount_percentage
        final_threshold = max(final_threshold, max_discount_threshold)
        
        return min(1.0, final_threshold)
    
    def _calculate_base_threshold(self, settings: BestOfferSettings) -> float:
        """Calculate base threshold from profit vs speed preference."""
        
        # Linear interpolation between initial and final thresholds
        preference = settings.profit_vs_speed_preference
        
        # Max speed (0.0) -> lower threshold for faster sales
        # Max profit (1.0) -> higher threshold for better margins
        min_threshold = settings.final_acceptance_threshold
        max_threshold = settings.initial_acceptance_threshold
        
        return min_threshold + (preference * (max_threshold - min_threshold))
    
    def _calculate_time_decay_factor(self, settings: BestOfferSettings, days_listed: int) -> float:
        """Calculate time decay factor to reduce threshold over time."""
        
        if days_listed <= settings.time_decay_days:
            return 1.0  # No decay yet
        
        # Linear decay from 1.0 to 0.85 over additional days
        max_decay_days = settings.time_decay_days * 2  # Double the decay period
        excess_days = min(days_listed - settings.time_decay_days, max_decay_days)
        decay_factor = 1.0 - (0.15 * (excess_days / max_decay_days))
        
        return max(0.85, decay_factor)
    
    def _calculate_inventory_factor(self, settings: BestOfferSettings, inventory: int) -> float:
        """Calculate inventory factor - lower threshold for high inventory."""
        
        if inventory >= settings.high_inventory_threshold:
            return 1.0 - settings.high_inventory_discount_bonus
        
        return 1.0
    
    def _calculate_performance_factor(self, listing_data: ListingData) -> float:
        """Calculate performance factor based on listing engagement."""
        
        # Low engagement -> lower threshold to encourage sales
        # High engagement -> maintain higher threshold
        
        views_per_day = listing_data.view_count / max(listing_data.days_listed, 1)
        watchers_per_day = listing_data.watcher_count / max(listing_data.days_listed, 1)
        
        # Simple heuristic - adjust based on engagement
        if views_per_day < 5 and watchers_per_day < 1:
            return 0.95  # Low engagement - reduce threshold slightly
        elif views_per_day > 20 or watchers_per_day > 5:
            return 1.05  # High engagement - can afford to be pickier
        
        return 1.0  # Normal engagement
    
    async def _calculate_counter_offer(
        self,
        settings: BestOfferSettings,
        listing_data: ListingData,
        offer: eBayOffer,
        acceptance_threshold: float
    ) -> float:
        """Calculate optimal counter offer amount."""
        
        # Counter at the acceptance threshold, but not higher than listing price
        counter_amount = listing_data.listing_price * acceptance_threshold
        
        # Round to reasonable increment ($0.50 for items under $100, $1 for higher)
        if counter_amount < 100:
            counter_amount = round(counter_amount * 2) / 2  # Round to nearest $0.50
        else:
            counter_amount = round(counter_amount)  # Round to nearest $1
        
        return min(counter_amount, listing_data.listing_price)
    
    async def _get_user_settings(self, user_id: str) -> Optional[BestOfferSettings]:
        """Get Best Offer settings for a user."""
        
        # Check cache first
        if user_id in self.active_settings:
            return self.active_settings[user_id]
        
        # Load from database
        try:
            settings = await self.marketplace_repository.get_best_offer_settings(user_id)
            if settings:
                self.active_settings[user_id] = settings
            return settings
        except Exception as e:
            logger.error(f"Error loading user settings: {e}")
            return None
    
    def _validate_settings(self, settings: BestOfferSettings) -> bool:
        """Validate Best Offer settings."""
        
        if not (0.0 <= settings.profit_vs_speed_preference <= 1.0):
            return False
        
        if not (0.0 <= settings.minimum_profit_margin <= 1.0):
            return False
        
        if not (0.0 <= settings.maximum_discount_percentage <= 1.0):
            return False
        
        if settings.initial_acceptance_threshold < settings.final_acceptance_threshold:
            return False
        
        return True
    
    async def get_offer_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get Best Offer performance statistics for a user."""
        
        try:
            stats = await self.marketplace_repository.get_offer_statistics(user_id, days)
            
            return {
                "total_offers_received": stats.get("total_offers", 0),
                "offers_accepted": stats.get("accepted", 0),
                "offers_declined": stats.get("declined", 0),
                "offers_countered": stats.get("countered", 0),
                "acceptance_rate": stats.get("acceptance_rate", 0.0),
                "average_accepted_percentage": stats.get("avg_accepted_pct", 0.0),
                "average_days_to_sale": stats.get("avg_days_to_sale", 0.0),
                "total_revenue": stats.get("total_revenue", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error getting offer statistics: {e}")
            return {}


# Utility functions for creating common settings presets
def create_speed_focused_settings() -> BestOfferSettings:
    """Create settings optimized for fast sales."""
    return BestOfferSettings(
        profit_vs_speed_preference=0.2,  # Favor speed
        minimum_profit_margin=0.10,      # Lower profit margin
        maximum_discount_percentage=0.35, # Allow larger discounts
        time_decay_enabled=True,
        time_decay_days=5,               # Faster decay
        final_acceptance_threshold=0.65   # Lower final threshold
    )


def create_profit_focused_settings() -> BestOfferSettings:
    """Create settings optimized for maximum profit."""
    return BestOfferSettings(
        profit_vs_speed_preference=0.8,  # Favor profit
        minimum_profit_margin=0.25,      # Higher profit margin
        maximum_discount_percentage=0.20, # Smaller discounts
        time_decay_enabled=True,
        time_decay_days=10,              # Slower decay
        final_acceptance_threshold=0.80   # Higher final threshold
    )


def create_balanced_settings() -> BestOfferSettings:
    """Create balanced settings for most users."""
    return BestOfferSettings(
        profit_vs_speed_preference=0.5,  # Balanced
        minimum_profit_margin=0.15,      # Reasonable profit margin
        maximum_discount_percentage=0.25, # Moderate discounts
        time_decay_enabled=True,
        time_decay_days=7,               # Standard decay
        final_acceptance_threshold=0.75   # Balanced threshold
    )
