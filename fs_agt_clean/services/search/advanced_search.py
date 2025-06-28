from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import numpy as np
from fuzzywuzzy import fuzz
from pydantic import BaseModel, ConfigDict
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from fs_agt_clean.core.metrics.service import MetricsService
from fs_agt_clean.core.service.asin_finder.models import ASINData
from fs_agt_clean.services.marketplace.amazon.service import AmazonService
from fs_agt_clean.services.marketplace.ebay.service import EbayService


class SearchParameters(BaseModel):
    keywords: List[str]
    category_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    condition: Optional[str] = None
    seller_rating: Optional[float] = None
    min_sales: Optional[int] = None
    sort_by: str = "relevance"
    marketplace: str = "US"


class SearchResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    title: str
    item_id: str
    category_id: str
    price: float
    condition: str
    seller: Dict[str, Any]
    aspects: Dict[str, List[str]]
    keywords_matched: List[str]
    relevance_score: float
    similarity_score: float
    competition_score: float


class AdvancedSearchEngine:

    def __init__(
        self,
        ebay_service: EbayService,
        amazon_service: AmazonService,
        metrics_service: MetricsService,
        min_similarity_score: float = 0.6,
        max_results: int = 100,
    ):
        self.ebay_service = ebay_service
        self.amazon_service = amazon_service
        self.metrics_service = metrics_service
        self.min_similarity_score = min_similarity_score
        self.max_results = max_results
        self.vectorizer = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 3), stop_words="english"
        )

    async def search(self, params: SearchParameters) -> List[SearchResult]:
        """Execute advanced search."""
        try:
            # Record search metrics
            await self.metrics_service.collect_metrics(
                {
                    "search_requests": 1.0,
                    "search_params_count": len(params.dict()),
                }
            )

            # Perform search
            raw_results = await self.ebay_service.search_items(
                keywords=" ".join(params.keywords), limit=self.max_results, sort="price"
            )

            # Process and filter results
            results = []
            error_count = 0
            for item in raw_results:
                try:
                    # Handle price conversion
                    price_value = item.get("price", {})
                    if isinstance(price_value, dict):
                        price = float(price_value.get("value", 0.0))
                    else:
                        price = float(price_value)

                    result = SearchResult(
                        title=item.get("title", ""),
                        item_id=str(item.get("itemId", item.get("id", ""))),
                        category_id=str(
                            item.get("categoryId", item.get("category_id", ""))
                        ),
                        price=price,
                        condition=item.get("condition", "UNKNOWN"),
                        seller=item.get("seller", {}),
                        aspects=item.get("aspects", {}),
                        keywords_matched=[],  # Will be populated by _process_results
                        relevance_score=0.0,  # Will be calculated by _process_results
                        similarity_score=0.0,  # Will be calculated by _process_results
                        competition_score=0.0,  # Will be calculated by _process_results
                    )
                    results.append(result)
                except (ValueError, TypeError) as e:
                    # Log error and skip invalid item
                    error_count += 1

            if error_count > 0:
                await self.metrics_service.collect_metrics(
                    {
                        "search_errors": float(error_count),
                        "price_conversion_errors": float(error_count),
                    }
                )

            # Process results to calculate scores
            processed_results = await self._process_results(results, params, None)
            sorted_results = self._sort_results(processed_results, params.sort_by)
            return sorted_results[: self.max_results]

        except Exception as e:
            # Record error metrics
            await self.metrics_service.track_error("search_error", str(e))
            raise

    async def _process_results(
        self,
        results: List[SearchResult],
        params: SearchParameters,
        asin_data: Optional[ASINData],
    ) -> List[SearchResult]:
        """Process search results with relevance scoring and competitor analysis."""
        processed_results = []
        titles = [result.title for result in results]
        if titles:
            tfidf_matrix = self.vectorizer.fit_transform(titles)
            tfidf_array = np.asarray(tfidf_matrix.todense())

        for idx, result in enumerate(results):
            relevance_score = self._calculate_relevance_score(
                result, params.keywords, tfidf_array[idx] if titles else None
            )
            similarity_score = (
                self._calculate_similarity_score(result, asin_data)
                if asin_data
                else 1.0
            )
            competition_score = self._calculate_competition_score(result)
            keywords_matched = self._extract_matched_keywords(
                result.title, params.keywords
            )

            # Update scores and matched keywords
            result.relevance_score = relevance_score
            result.similarity_score = similarity_score
            result.competition_score = competition_score
            result.keywords_matched = keywords_matched

            if similarity_score >= self.min_similarity_score:
                processed_results.append(result)

        return processed_results

    def _calculate_relevance_score(
        self,
        result: Union[SearchResult, Dict[str, Any]],
        keywords: List[str],
        tfidf_vector: Optional[np.ndarray],
    ) -> float:
        """Calculate relevance score based on multiple factors."""
        scores = []

        # Get title safely whether result is a SearchResult or dict
        title = (
            result.title
            if isinstance(result, SearchResult)
            else str(result.get("title", ""))
        )

        # Calculate title match score
        title_score = (
            max(fuzz.partial_ratio(title.lower(), kw.lower()) for kw in keywords)
            / 100.0
        )
        scores.append(title_score * 0.4)

        # Add TF-IDF score if available
        if tfidf_vector is not None:
            tfidf_score = float(np.mean(tfidf_vector))
            scores.append(tfidf_score * 0.3)

        # Add exact match bonus
        exact_matches = sum(1 for kw in keywords if kw.lower() in title.lower())
        exact_match_score = exact_matches / len(keywords) if keywords else 0
        scores.append(exact_match_score * 0.3)

        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_similarity_score(
        self, result: SearchResult, asin_data: ASINData
    ) -> float:
        """Calculate similarity score between eBay item and Amazon ASIN."""
        if not asin_data:
            return 1.0

        scores = []
        title_similarity = (
            fuzz.ratio(result.title.lower(), asin_data.product_name.lower()) / 100.0
        )
        scores.append(title_similarity * 0.4)

        price_diff = abs(result.price - asin_data.price)
        price_similarity = max(0, 1 - price_diff / asin_data.price)
        scores.append(price_similarity * 0.3)

        category_similarity = float(
            result.category_id == asin_data.category if asin_data.category else 1.0
        )
        scores.append(category_similarity * 0.3)

        return sum(scores)

    def _calculate_competition_score(
        self, result: Union[SearchResult, Dict[str, Any]]
    ) -> float:
        """Calculate competition score based on seller metrics."""
        try:
            # Get seller data safely
            seller_data = (
                result.seller
                if isinstance(result, SearchResult)
                else result.get("seller", {})
            )
            if not isinstance(seller_data, dict):
                seller_data = {}

            # Calculate individual components
            feedback_score = min(
                float(seller_data.get("feedback_score", 0)) / 10000, 1.0
            )
            positive_feedback = (
                float(seller_data.get("positive_feedback_percent", 0)) / 100
            )
            seller_level = {
                "TOP_RATED": 1.0,
                "ABOVE_AVERAGE": 0.8,
                "AVERAGE": 0.6,
                "BELOW_AVERAGE": 0.4,
                "NEW": 0.3,
            }.get(str(seller_data.get("level", "NEW")).upper(), 0.3)

            # Combine scores with weights
            scores = [
                (feedback_score, 0.4),
                (positive_feedback, 0.4),
                (seller_level, 0.2),
            ]

            return sum(score * weight for score, weight in scores)
        except (ValueError, TypeError, AttributeError):
            return 0.0

    def _extract_matched_keywords(self, title: str, keywords: List[str]) -> List[str]:
        """
        Extract keywords that match in the title using fuzzy matching.
        """
        matched = []
        title_lower = title.lower()
        for keyword in keywords:
            if fuzz.partial_ratio(title_lower, keyword.lower()) >= 80:
                matched.append(keyword)
        return matched

    def _sort_results(
        self, results: List[SearchResult], sort_by: str
    ) -> List[SearchResult]:
        """
        Sort results based on specified criteria.
        """
        if sort_by == "relevance":
            return sorted(results, key=lambda x: x.relevance_score, reverse=True)
        elif sort_by == "price_asc":
            return sorted(results, key=lambda x: x.price)
        elif sort_by == "price_desc":
            return sorted(results, key=lambda x: x.price, reverse=True)
        elif sort_by == "competition":
            return sorted(results, key=lambda x: x.competition_score, reverse=True)
        else:
            return results
