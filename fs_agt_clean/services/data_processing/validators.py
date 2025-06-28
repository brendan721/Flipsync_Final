import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.services.data_pipeline.models import ProductData, ValidationResult

"\nValidation layer for incoming product data.\n"


@dataclass
class ValidationRule:
    field: str
    rule_type: str
    parameters: Dict
    error_message: str


class DataValidator:
    """Base class for data validators."""

    def __init__(self):
        self.rules: List[ValidationRule] = self._init_rules()
        self.logger = logging.getLogger(__name__)

    def _init_rules(self) -> List[ValidationRule]:
        """Initialize validation rules."""
        return [
            ValidationRule(
                field="asin",
                rule_type="pattern",
                parameters={"pattern": "^[A-Z0-9]{10}$"},
                error_message="Invalid ASIN format",
            ),
            ValidationRule(
                field="price",
                rule_type="range",
                parameters={"min": 0.01, "max": 999999.99},
                error_message="Price out of valid range",
            ),
            ValidationRule(
                field="timestamp",
                rule_type="timestamp",
                parameters={},
                error_message="Invalid timestamp format",
            ),
        ]

    async def validate_product(self, product: ProductData) -> ValidationResult:
        """Validate product data."""
        if not product:
            return ValidationResult(
                is_valid=False,
                errors=["Product data is None"],
                product_id="unknown",
                validated_data=None,
            )

        errors: List[str] = []

        # Basic validation rules
        if not product.asin:
            errors.append("Missing ASIN")
        if not product.title:
            errors.append("Missing title")
        if product.price <= 0:
            errors.append("Price out of valid range")
        if not product.description:
            errors.append("Missing description")
        if not product.brand:
            errors.append("Missing brand")
        if not product.category:
            errors.append("Missing category")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            product_id=product.asin if hasattr(product, "asin") else "unknown",
            validated_data=product if len(errors) == 0 else None,
        )

    async def validate_batch(
        self, products: List[ProductData]
    ) -> List[ValidationResult]:
        """Validate a batch of products."""
        results = []
        for product in products:
            result = await self.validate_product(product)
            results.append(result)
        return results

    def _check_rule(
        self, product: Union[ProductData, Dict[str, Any]], rule: ValidationRule
    ) -> bool:
        """Check a single validation rule against a product."""
        if isinstance(product, dict):
            value = product.get(rule.field)
        else:
            value = getattr(product, rule.field, None)

        if value is None:
            return bool(False)

        if rule.rule_type == "pattern":
            return bool(re.match(rule.parameters["pattern"], str(value)))
        elif rule.rule_type == "range":
            try:
                float_value = float(value)
                return rule.parameters["min"] <= float_value <= rule.parameters["max"]
            except (ValueError, TypeError):
                return False
        elif rule.rule_type == "timestamp":
            try:
                if isinstance(value, str):
                    datetime.fromisoformat(value)
                return True
            except (ValueError, TypeError):
                return False
        return False

    async def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a data item.

        Args:
            data: Data item to validate

        Returns:
            ValidationResult: Result of validation
        """
        try:
            if isinstance(data, ProductData):
                return await self.validate_product(data)

            errors = []
            for rule in self.rules:
                if rule.field in data and not self._check_rule(data, rule):
                    errors.append(rule.error_message)

            # Convert dict to ProductData if validation passes
            validated_data = None
            if len(errors) == 0:
                try:
                    validated_data = ProductData(
                        asin=data.get("asin", ""),
                        title=data.get("title", ""),
                        price=float(data.get("price", 0)),
                        description=data.get("description", ""),
                        features=data.get("features", []),
                        brand=data.get("brand", ""),
                        category=data.get("category", ""),
                        images=data.get("images", []),
                        metadata=data.get("metadata", {}),
                    )
                except Exception as e:
                    errors.append(f"Failed to create ProductData: {str(e)}")

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                product_id=str(data.get("id", data.get("asin", "unknown"))),
                validated_data=validated_data,
            )
        except Exception as e:
            self.logger.error("Validation error: %s", str(e))
            return ValidationResult(
                is_valid=False,
                errors=[str(e)],
                product_id=str(data.get("id", data.get("asin", "unknown"))),
                validated_data=None,
            )
