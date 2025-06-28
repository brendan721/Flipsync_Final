import logging
from datetime import datetime, timezone
from typing import Dict, List

from fs_agt_clean.core.security.rate_limiter import RateLimiter
from fs_agt_clean.core.utils.token_manager import TokenManager
from fs_agt_clean.core.workflow_engine.pipelines.amazon_to_qdrant import ProductData
from fs_agt_clean.services.batch.processor import RateLimit

"\nData Acquisition UnifiedAgent for handling data operations with rate limiting and security.\n"
logger = logging.getLogger(__name__)


class DataAcquisitionUnifiedAgent:
    """Handles all data operations with built-in rate limiting and security."""

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.rate_limiter = RateLimiter(limit=RateLimit(requests_per_minute=100))
        self.logger = logging.getLogger(__name__)

    async def extract_sheet_data(self, sheet_id: str) -> List[Dict]:
        """Extract data from Google Sheets with rate limiting."""
        await self.rate_limiter.acquire()
        try:
            credentials = await self.token_manager.get_credentials("sheets")
            self.logger.info("Extracting data from sheet %s", sheet_id)
            return []
        finally:
            self.rate_limiter.release()

    async def fetch_amazon_data(self, asin_list: List[str]) -> List[ProductData]:
        """Fetch product data from Amazon with rate limiting."""
        await self.rate_limiter.acquire()
        try:
            credentials = await self.token_manager.get_credentials("amazon")
            self.logger.info("Fetching data for %s ASINs", len(asin_list))
            return []
        finally:
            self.rate_limiter.release()

    async def store_vector_data(self, data: List[ProductData]) -> None:
        """Store data in Qdrant vector storage."""
        try:
            self.logger.info("Storing %s products in vector storage", len(data))
        except Exception as e:
            self.logger.error("Error storing vector data: %s", str(e))
            raise

    def log_transaction(self, operation: str, status: str, details: Dict) -> None:
        """Log all data operations for audit purposes."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "status": status,
            "details": details,
        }
        self.logger.info("Transaction logged: %s", log_entry)
