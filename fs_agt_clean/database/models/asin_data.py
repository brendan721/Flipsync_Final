"""
ASIN data models for Amazon product information.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ASINData(BaseModel):
    """Amazon Standard Identification Number (ASIN) data model."""

    asin: str = Field(..., description="Amazon Standard Identification Number")
    title: str = Field(..., description="Product title")
    brand: Optional[str] = Field(None, description="Product brand")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[float] = Field(None, description="Product price")
    currency: Optional[str] = Field(None, description="Price currency")
    images: Optional[List[str]] = Field(None, description="Product images URLs")
    features: Optional[List[str]] = Field(None, description="Product features")
    categories: Optional[List[str]] = Field(None, description="Product categories")
    rating: Optional[float] = Field(None, description="Product rating")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    availability: Optional[str] = Field(None, description="Product availability status")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "asin": "B07PXGQC1Q",
                "title": "Echo Dot (3rd Gen) - Smart speaker with Alexa",
                "brand": "Amazon",
                "description": "Use your voice to play music, answer questions, read the news, check the weather, set alarms, control compatible smart home devices, and more.",
                "price": 39.99,
                "currency": "USD",
                "images": [
                    "https://images-na.ssl-images-amazon.com/images/I/61MZfO8hGgL._SL1000_.jpg"
                ],
                "features": [
                    "Voice control your music",
                    "Control your smart home",
                    "Make calls and send messages",
                ],
                "categories": ["Electronics", "Smart Home", "Speakers"],
                "rating": 4.7,
                "review_count": 193651,
                "availability": "In Stock",
            }
        }


class ASINSearchRequest(BaseModel):
    """Request model for ASIN search."""

    query: str = Field(..., description="Search query")
    marketplace: Optional[str] = Field("US", description="Amazon marketplace")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"example": {"query": "echo dot", "marketplace": "US"}}


class ASINSearchResponse(BaseModel):
    """Response model for ASIN search."""

    results: List[ASINData] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "asin": "B07PXGQC1Q",
                        "title": "Echo Dot (3rd Gen) - Smart speaker with Alexa",
                        "brand": "Amazon",
                        "price": 39.99,
                        "currency": "USD",
                        "rating": 4.7,
                        "review_count": 193651,
                        "availability": "In Stock",
                    }
                ],
                "total": 1,
            }
        }
