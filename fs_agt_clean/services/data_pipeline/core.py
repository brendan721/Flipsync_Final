"""Data pipeline core implementation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, TypedDict

from fs_agt_clean.services.llm.ollama_service import OllamaLLMService
from fs_agt_clean.services.qdrant.service import QdrantService


class ProcessResult(TypedDict):
    """Type definition for process result."""

    status: str
    error: Optional[str]
    embedding: Optional[List[float]]
    id: Optional[str]


class DataPipelineCore:
    """Core implementation for data processing pipeline."""

    def __init__(
        self,
        config_manager: Any,
        llm_service: OllamaLLMService,
        vector_store: QdrantService,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the pipeline core."""
        self.config_manager = config_manager
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)

    async def process_item(self, item: Dict[str, Any]) -> ProcessResult:
        """Process a single item."""
        if not self._validate_item(item):
            return ProcessResult(
                status="error",
                error="Validation failed: missing required fields",
                embedding=None,
                id=item.get("id"),
            )

        for attempt in range(self.max_retries):
            try:
                # Get embeddings from LLM service
                embedding = await self.llm_service.get_embeddings(item["text"])
                if not embedding:
                    return ProcessResult(
                        status="error",
                        error="Failed to generate embeddings",
                        embedding=None,
                        id=item.get("id"),
                    )

                # Store vectors in vector store
                await self.vector_store.store_vectors(
                    vectors=[
                        {
                            "id": item["id"],
                            "vector": embedding,
                            "payload": {
                                "text": item["text"],
                                "metadata": item.get("metadata", {}),
                            },
                        }
                    ]
                )

                return ProcessResult(
                    status="success", error=None, embedding=embedding, id=item["id"]
                )

            except Exception as e:
                self.logger.error(f"Error processing item {item.get('id')}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue

                return ProcessResult(
                    status="error", error=str(e), embedding=None, id=item.get("id")
                )

    async def process_batch(self, items: List[Dict[str, Any]]) -> List[ProcessResult]:
        """Process a batch of items."""
        return [await self.process_item(item) for item in items]

    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate input item."""
        required_fields = ["id", "text"]
        return all(field in item for field in required_fields)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Add cleanup logic if needed
        pass
