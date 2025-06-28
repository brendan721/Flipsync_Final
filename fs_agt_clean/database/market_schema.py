from typing import Any, Dict, List

from fs_agt_clean.services.market.validation_framework.core_validation import (
    BaseValidator,
    ValidationContext,
    ValidationLevel,
    ValidationResult,
)


def create_market_schema() -> Dict[str, Any]:
    """Create a schema for market data validation"""
    return {
        "type": "object",
        "properties": {
            "total_listings": {"type": "integer", "minimum": 0},
            "active_listings": {"type": "integer", "minimum": 0},
            "avg_price": {"type": "number", "minimum": 0},
            "min_price": {"type": "number", "minimum": 0},
            "max_price": {"type": "number", "minimum": 0},
            "avg_rating": {"type": "number", "minimum": 0, "maximum": 5},
            "total_reviews": {"type": "integer", "minimum": 0},
        },
        "required": [
            "total_listings",
            "active_listings",
            "avg_price",
            "min_price",
            "max_price",
            "avg_rating",
            "total_reviews",
        ],
    }


def create_competitor_schema() -> Dict[str, Any]:
    """Create a schema for competitor data validation"""
    return {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "total_listings": {"type": "integer", "minimum": 0},
            "avg_price": {"type": "number", "minimum": 0},
            "market_share": {"type": "number", "minimum": 0, "maximum": 1},
            "avg_rating": {"type": "number", "minimum": 0, "maximum": 5},
            "total_reviews": {"type": "integer", "minimum": 0},
        },
        "required": [
            "id",
            "name",
            "total_listings",
            "avg_price",
            "market_share",
            "avg_rating",
            "total_reviews",
        ],
    }


class MarketDataValidator(BaseValidator):

    def __init__(self):
        super().__init__("market_data_validator")
        self.schema = create_market_schema()

    async def validate(self, context: ValidationContext) -> List[ValidationResult]:
        """Validate market data against schema"""
        results = []
        data = context.data
        for field in self.schema["required"]:
            if field not in data:
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Missing required field: {field}",
                        context={"field": field},
                    )
                )
        for field, value in data.items():
            field_schema = self.schema["properties"].get(field)
            if not field_schema:
                continue
            if field_schema["type"] == "number" and (
                not isinstance(value, (int, float))
            ):
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Field {field} must be a number",
                        context={"field": field, "value": value},
                    )
                )
            elif field_schema["type"] == "integer" and (not isinstance(value, int)):
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Field {field} must be an integer",
                        context={"field": field, "value": value},
                    )
                )
            if "minimum" in field_schema and value < field_schema["minimum"]:
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Field {field} must be >= {field_schema['minimum']}",
                        context={
                            "field": field,
                            "value": value,
                            "minimum": field_schema["minimum"],
                        },
                    )
                )
            if "maximum" in field_schema and value > field_schema["maximum"]:
                results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Field {field} must be <= {field_schema['maximum']}",
                        context={
                            "field": field,
                            "value": value,
                            "maximum": field_schema["maximum"],
                        },
                    )
                )
        return results
