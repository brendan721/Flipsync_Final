from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

"\nData models and schemas for the pipeline.\n"


class DataStage(Enum):
    """Pipeline processing stages."""

    ACQUISITION = auto()
    VALIDATION = auto()
    TRANSFORMATION = auto()
    ENRICHMENT = auto()
    STORAGE = auto()


@dataclass
class ProductData:
    """Product data model."""

    asin: str
    title: str
    price: float
    description: str
    features: List[str]
    brand: str
    category: str
    images: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "asin": self.asin,
            "title": self.title,
            "price": self.price,
            "description": self.description,
            "features": self.features,
            "brand": self.brand,
            "category": self.category,
            "images": self.images,
            "metadata": self.metadata,
        }

    def copy(self) -> "ProductData":
        """Create a copy of the product data."""
        return ProductData(
            asin=self.asin,
            title=self.title,
            price=self.price,
            description=self.description,
            features=self.features.copy(),
            brand=self.brand,
            category=self.category,
            images=self.images.copy(),
            metadata=self.metadata.copy(),
        )


@dataclass
class ValidationResult:
    """Validation result model."""

    is_valid: bool
    errors: List[str]
    product_id: str
    validated_data: Optional[ProductData] = None


@dataclass
class TransformationResult:
    """Transformation result model."""

    success: bool
    transformed_data: Optional[ProductData]
    error_message: Optional[str]
    original_data: Dict[str, Any]
    transformation_type: str
    timestamp: Optional[datetime] = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "transformed_data": (
                self.transformed_data.to_dict() if self.transformed_data else None
            ),
            "error_message": self.error_message,
            "original_data": self.original_data,
            "transformation_type": self.transformation_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_sheet_row(cls, row: List[str]) -> "TransformationResult":
        """Create TransformationResult instance from Google Sheets row."""
        # TODO: Implement sheet row conversion
        raise NotImplementedError()

    @classmethod
    def from_amazon_response(cls, response: Dict[str, Any]) -> "TransformationResult":
        """Create TransformationResult instance from Amazon API response."""
        return cls(
            success=True,
            transformed_data=ProductData(
                asin=response["asin"],
                title=response["title"],
                price=float(response["price"]),
                description=response.get("description", ""),
                features=response.get("features", []),
                brand=response.get("brand", ""),
                category=response.get("category", ""),
                images=response.get("images", []),
                metadata=response.get("metadata", {}),
            ),
            error_message=None,
            original_data=response,
            transformation_type="Amazon API response",
        )

    def copy(self) -> "TransformationResult":
        """Create a deep copy of the TransformationResult instance."""
        return TransformationResult(
            success=self.success,
            transformed_data=(
                self.transformed_data.copy() if self.transformed_data else None
            ),
            error_message=self.error_message,
            original_data=self.original_data.copy(),
            transformation_type=self.transformation_type,
            timestamp=self.timestamp,
        )
