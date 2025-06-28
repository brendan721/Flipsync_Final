from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class CompetitorProfile:
    seller_id: str
    price: float
    rating: float
    review_count: int
    fulfillment_type: str
    last_updated: datetime

    @property
    def threat_level(self) -> str:
        """Calculate threat level based on competitor metrics."""
        # Higher threat if they have good ratings and reviews
        rating_factor = self.rating >= 4.0
        review_factor = self.review_count >= 50
        fulfillment_factor = self.fulfillment_type == "FBA"

        if rating_factor and review_factor and fulfillment_factor:
            return "high"
        elif rating_factor or (review_factor and fulfillment_factor):
            return "medium"
        else:
            return "low"
