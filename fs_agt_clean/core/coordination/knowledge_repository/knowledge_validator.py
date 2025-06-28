"""
Knowledge validator for the knowledge repository.

This module provides interfaces and implementations for validating knowledge
items before they are added to the knowledge repository.
"""

import abc
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.knowledge_repository.knowledge_repository import (
    KnowledgeError,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
)
from fs_agt_clean.core.monitoring import get_logger


class ValidationError(Exception):
    """Base exception for knowledge validation errors."""

    def __init__(
        self,
        message: str,
        knowledge_id: Optional[str] = None,
        field: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize a validation error.

        Args:
            message: Error message
            knowledge_id: ID of the knowledge item related to the error
            field: Field that failed validation
            cause: Original exception that caused this error
        """
        self.message = message
        self.knowledge_id = knowledge_id
        self.field = field
        self.cause = cause

        # Create a detailed error message
        detailed_message = message
        if knowledge_id:
            detailed_message += f" (knowledge_id: {knowledge_id})"
        if field:
            detailed_message += f" (field: {field})"
        if cause:
            detailed_message += f" - caused by: {str(cause)}"

        super().__init__(detailed_message)


class KnowledgeValidator(abc.ABC):
    """
    Interface for knowledge validators.

    Knowledge validators validate knowledge items before they are added
    to the knowledge repository.
    """

    @abc.abstractmethod
    async def validate(self, knowledge: KnowledgeItem) -> bool:
        """
        Validate a knowledge item.

        Args:
            knowledge: Knowledge item to validate

        Returns:
            True if the knowledge item is valid

        Raises:
            ValidationError: If the knowledge item is invalid
        """
        pass

    @abc.abstractmethod
    async def validate_batch(self, knowledge_items: List[KnowledgeItem]) -> List[bool]:
        """
        Validate multiple knowledge items.

        Args:
            knowledge_items: Knowledge items to validate

        Returns:
            List of validation results (True for valid, False for invalid)
        """
        pass


class SchemaValidator(KnowledgeValidator):
    """
    Schema-based knowledge validator.

    This validator validates knowledge items against JSON schemas.
    """

    def __init__(
        self, validator_id: str, schemas: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Initialize a schema validator.

        Args:
            validator_id: Unique identifier for this validator
            schemas: Dictionary mapping topic patterns to JSON schemas
        """
        self.validator_id = validator_id
        self.logger = get_logger(f"knowledge_validator.{validator_id}")
        self.schemas = schemas or {}
        self.topic_patterns = {
            re.compile(pattern): schema for pattern, schema in self.schemas.items()
        }

    def add_schema(self, topic_pattern: str, schema: Dict[str, Any]) -> None:
        """
        Add a schema for a topic pattern.

        Args:
            topic_pattern: Regex pattern for topics
            schema: JSON schema for validation
        """
        self.schemas[topic_pattern] = schema
        self.topic_patterns[re.compile(topic_pattern)] = schema

    def remove_schema(self, topic_pattern: str) -> bool:
        """
        Remove a schema for a topic pattern.

        Args:
            topic_pattern: Regex pattern for topics

        Returns:
            True if the schema was removed
        """
        if topic_pattern in self.schemas:
            del self.schemas[topic_pattern]
            self.topic_patterns = {
                re.compile(pattern): schema for pattern, schema in self.schemas.items()
            }
            return True
        return False

    async def validate(self, knowledge: KnowledgeItem) -> bool:
        """
        Validate a knowledge item.

        Args:
            knowledge: Knowledge item to validate

        Returns:
            True if the knowledge item is valid

        Raises:
            ValidationError: If the knowledge item is invalid
        """
        try:
            # Check if the knowledge item has content
            if knowledge.content is None:
                raise ValidationError(
                    "Knowledge item has no content",
                    knowledge_id=knowledge.knowledge_id,
                    field="content",
                )

            # Find a matching schema for the topic
            schema = None
            for pattern, s in self.topic_patterns.items():
                if pattern.search(knowledge.topic):
                    schema = s
                    break

            # If no schema is found, the item is valid
            if schema is None:
                return True

            # Validate the content against the schema
            # This is a simplified implementation
            # In a real implementation, use a proper JSON schema validator
            if isinstance(knowledge.content, dict):
                # Check required fields
                required = schema.get("required", [])
                for field in required:
                    if field not in knowledge.content:
                        raise ValidationError(
                            f"Required field '{field}' is missing",
                            knowledge_id=knowledge.knowledge_id,
                            field=field,
                        )

                # Check field types
                properties = schema.get("properties", {})
                for field, value in knowledge.content.items():
                    if field in properties:
                        field_type = properties[field].get("type")
                        if field_type == "string" and not isinstance(value, str):
                            raise ValidationError(
                                f"Field '{field}' should be a string",
                                knowledge_id=knowledge.knowledge_id,
                                field=field,
                            )
                        elif field_type == "number" and not isinstance(
                            value, (int, float)
                        ):
                            raise ValidationError(
                                f"Field '{field}' should be a number",
                                knowledge_id=knowledge.knowledge_id,
                                field=field,
                            )
                        elif field_type == "boolean" and not isinstance(value, bool):
                            raise ValidationError(
                                f"Field '{field}' should be a boolean",
                                knowledge_id=knowledge.knowledge_id,
                                field=field,
                            )
                        elif field_type == "array" and not isinstance(value, list):
                            raise ValidationError(
                                f"Field '{field}' should be an array",
                                knowledge_id=knowledge.knowledge_id,
                                field=field,
                            )
                        elif field_type == "object" and not isinstance(value, dict):
                            raise ValidationError(
                                f"Field '{field}' should be an object",
                                knowledge_id=knowledge.knowledge_id,
                                field=field,
                            )

            return True
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            error_msg = f"Failed to validate knowledge item: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValidationError(
                error_msg, knowledge_id=knowledge.knowledge_id, cause=e
            )

    async def validate_batch(self, knowledge_items: List[KnowledgeItem]) -> List[bool]:
        """
        Validate multiple knowledge items.

        Args:
            knowledge_items: Knowledge items to validate

        Returns:
            List of validation results (True for valid, False for invalid)
        """
        results = []
        for knowledge in knowledge_items:
            try:
                valid = await self.validate(knowledge)
                results.append(valid)
            except ValidationError:
                results.append(False)

        return results
