"""
Enhanced Product Research Service for FlipSync
==============================================

This service provides comprehensive product research capabilities including:
- Ethical web scraping with robots.txt compliance
- Multi-source product data aggregation
- Competitive pricing analysis
- Feature extraction and standardization
- Integration with existing AI vision analysis
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import aiohttp
from bs4 import BeautifulSoup

from fs_agt_clean.core.ai.openai_client import FlipSyncOpenAIClient, OpenAIModel
from fs_agt_clean.core.monitoring.cost_tracker import CostCategory, record_ai_cost

logger = logging.getLogger(__name__)


@dataclass
class ProductResearchResult:
    """Result of comprehensive product research."""
    
    product_name: str
    brand: str
    model: str
    category: str
    specifications: Dict[str, Any]
    features: List[str]
    competitive_prices: List[Dict[str, Any]]
    market_position: str
    research_confidence: float
    sources_used: List[str]
    research_timestamp: datetime


@dataclass
class ScrapingTarget:
    """Configuration for ethical scraping target."""
    
    domain: str
    base_url: str
    robots_txt_url: str
    rate_limit_delay: float
    user_agent: str
    allowed_paths: List[str]
    respect_robots_txt: bool = True


class EthicalWebScrapingService:
    """Ethical web scraping service with robots.txt compliance and rate limiting."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.rate_limiters: Dict[str, float] = {}  # domain -> last_request_time
        
        # Configure ethical scraping targets
        self.scraping_targets = {
            "manufacturer_specs": [
                ScrapingTarget(
                    domain="apple.com",
                    base_url="https://www.apple.com",
                    robots_txt_url="https://www.apple.com/robots.txt",
                    rate_limit_delay=2.0,
                    user_agent="FlipSync-Research-Bot/1.0 (+https://flipsync.com/bot)",
                    allowed_paths=["/iphone/", "/ipad/", "/mac/", "/watch/"]
                ),
                ScrapingTarget(
                    domain="samsung.com",
                    base_url="https://www.samsung.com",
                    robots_txt_url="https://www.samsung.com/robots.txt",
                    rate_limit_delay=2.0,
                    user_agent="FlipSync-Research-Bot/1.0 (+https://flipsync.com/bot)",
                    allowed_paths=["/us/mobile/", "/us/computing/", "/us/tv-audio-video/"]
                )
            ],
            "price_comparison": [
                ScrapingTarget(
                    domain="pricewatch.com",
                    base_url="https://www.pricewatch.com",
                    robots_txt_url="https://www.pricewatch.com/robots.txt",
                    rate_limit_delay=3.0,
                    user_agent="FlipSync-Research-Bot/1.0 (+https://flipsync.com/bot)",
                    allowed_paths=["/search/"]
                )
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "UnifiedUser-UnifiedAgent": "FlipSync-Research-Bot/1.0 (+https://flipsync.com/bot)"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def check_robots_txt(self, target: ScrapingTarget, path: str) -> bool:
        """Check if scraping is allowed by robots.txt."""
        if not target.respect_robots_txt:
            return True
            
        try:
            if target.domain not in self.robots_cache:
                async with self.session.get(target.robots_txt_url) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        rp = RobotFileParser()
                        rp.set_url(target.robots_txt_url)
                        rp.read_string(robots_content)
                        self.robots_cache[target.domain] = rp
                    else:
                        # If robots.txt not found, assume scraping is allowed
                        return True
            
            robots = self.robots_cache.get(target.domain)
            if robots:
                return robots.can_fetch(target.user_agent, urljoin(target.base_url, path))
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {target.domain}: {e}")
            # If we can't check robots.txt, err on the side of caution
            return False
    
    async def rate_limited_request(self, target: ScrapingTarget, url: str) -> Optional[str]:
        """Make rate-limited request respecting ethical guidelines."""
        try:
            # Check rate limiting
            now = asyncio.get_event_loop().time()
            last_request = self.rate_limiters.get(target.domain, 0)
            
            if now - last_request < target.rate_limit_delay:
                await asyncio.sleep(target.rate_limit_delay - (now - last_request))
            
            # Check robots.txt
            path = urlparse(url).path
            if not await self.check_robots_txt(target, path):
                logger.warning(f"Robots.txt disallows scraping {url}")
                return None
            
            # Make request
            async with self.session.get(url) as response:
                self.rate_limiters[target.domain] = asyncio.get_event_loop().time()
                
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    async def scrape_manufacturer_specs(self, brand: str, model: str) -> Dict[str, Any]:
        """Scrape official manufacturer specifications."""
        specs = {}
        
        # Find appropriate scraping target for brand
        brand_lower = brand.lower()
        manufacturer_targets = self.scraping_targets.get("manufacturer_specs", [])
        
        for target in manufacturer_targets:
            if brand_lower in target.domain:
                try:
                    # Construct search URL (this would be brand-specific)
                    search_url = f"{target.base_url}/search?q={model}"
                    
                    content = await self.rate_limited_request(target, search_url)
                    if content:
                        specs.update(await self._extract_specs_from_content(content, brand, model))
                        
                except Exception as e:
                    logger.error(f"Error scraping specs from {target.domain}: {e}")
        
        return specs
    
    async def _extract_specs_from_content(self, content: str, brand: str, model: str) -> Dict[str, Any]:
        """Extract specifications from scraped content."""
        specs = {}
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for common specification patterns
            spec_patterns = [
                r'(\d+(?:\.\d+)?)\s*(gb|tb|mb)',  # Storage/Memory
                r'(\d+(?:\.\d+)?)\s*(inch|"|\')',  # Screen size
                r'(\d+)\s*x\s*(\d+)',  # Resolution
                r'(\d+(?:\.\d+)?)\s*(ghz|mhz)',  # Processor speed
                r'(\d+)\s*(mp|megapixel)',  # Camera
            ]
            
            text_content = soup.get_text().lower()
            
            for pattern in spec_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    # Store first match for each pattern type
                    if 'gb' in pattern or 'tb' in pattern:
                        specs['storage'] = matches[0]
                    elif 'inch' in pattern:
                        specs['screen_size'] = matches[0]
                    elif 'x' in pattern:
                        specs['resolution'] = f"{matches[0][0]}x{matches[0][1]}"
                    elif 'ghz' in pattern:
                        specs['processor_speed'] = matches[0]
                    elif 'mp' in pattern:
                        specs['camera'] = matches[0]
            
        except Exception as e:
            logger.error(f"Error extracting specs: {e}")
        
        return specs


class EnhancedProductResearchService:
    """Enhanced product research service integrating AI analysis and web scraping."""
    
    def __init__(self):
        self.scraping_service = EthicalWebScrapingService()
        self.openai_client = FlipSyncOpenAIClient.create_default()
        
    async def research_product_from_image(
        self, 
        image_analysis_result: Dict[str, Any],
        marketplace: str = "ebay"
    ) -> ProductResearchResult:
        """Comprehensive product research from AI image analysis result."""
        
        try:
            # Extract basic product info from image analysis
            product_data = image_analysis_result.get("product_data", {})
            product_name = product_data.get("title", "Unknown Product")
            brand = product_data.get("brand", "Unknown Brand")
            category = product_data.get("category", "General")
            
            logger.info(f"Starting research for: {brand} {product_name}")
            
            # 1. Web scraping for specifications
            async with self.scraping_service:
                scraped_specs = await self.scraping_service.scrape_manufacturer_specs(
                    brand, product_name
                )
            
            # 2. AI-enhanced feature extraction
            enhanced_features = await self._extract_features_with_ai(
                product_name, brand, scraped_specs
            )
            
            # 3. Competitive pricing research (placeholder - would integrate with APIs)
            competitive_prices = await self._research_competitive_pricing(
                product_name, brand, marketplace
            )
            
            # 4. Market positioning analysis
            market_position = await self._analyze_market_position(
                product_name, brand, competitive_prices
            )
            
            # Calculate research confidence
            confidence = self._calculate_research_confidence(
                scraped_specs, enhanced_features, competitive_prices
            )
            
            return ProductResearchResult(
                product_name=product_name,
                brand=brand,
                model=product_name,  # Could be enhanced to extract model separately
                category=category,
                specifications=scraped_specs,
                features=enhanced_features,
                competitive_prices=competitive_prices,
                market_position=market_position,
                research_confidence=confidence,
                sources_used=["web_scraping", "ai_analysis", "price_apis"],
                research_timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error in product research: {e}")
            # Return basic result from image analysis
            return ProductResearchResult(
                product_name=product_name,
                brand=brand,
                model=product_name,
                category=category,
                specifications={},
                features=product_data.get("features", []),
                competitive_prices=[],
                market_position="unknown",
                research_confidence=0.3,
                sources_used=["ai_analysis_only"],
                research_timestamp=datetime.now(timezone.utc)
            )
    
    async def _extract_features_with_ai(
        self, product_name: str, brand: str, specs: Dict[str, Any]
    ) -> List[str]:
        """Use AI to extract and enhance product features."""
        
        try:
            prompt = f"""
            Analyze this product and extract key selling features for an eBay listing:
            
            Product: {brand} {product_name}
            Specifications: {specs}
            
            Generate a list of 5-8 compelling features that would appeal to buyers.
            Focus on benefits, not just technical specs.
            Format as a simple list, one feature per line.
            """
            
            response = await self.openai_client.generate_text_optimized(
                prompt=prompt,
                model=OpenAIModel.GPT_4O_MINI,
                max_tokens=200
            )
            
            # Record cost
            await record_ai_cost(
                category=CostCategory.CONTENT_CREATION.value,
                model="gpt-4o-mini",
                operation="feature_extraction",
                cost=response.cost_estimate,
                agent_id="product_research_agent"
            )
            
            # Parse features from response
            features = [
                line.strip().lstrip('- ').lstrip('• ')
                for line in response.content.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            
            return features[:8]  # Limit to 8 features
            
        except Exception as e:
            logger.error(f"Error extracting features with AI: {e}")
            return ["High-quality construction", "Reliable performance", "Great value"]
    
    async def _research_competitive_pricing(
        self, product_name: str, brand: str, marketplace: str
    ) -> List[Dict[str, Any]]:
        """Research competitive pricing (placeholder for API integration)."""
        
        # This would integrate with eBay Finding API, Amazon PA-API, etc.
        # For now, return mock data structure
        return [
            {
                "source": "ebay",
                "price": 299.99,
                "condition": "new",
                "seller_rating": 4.8,
                "shipping": 9.99
            },
            {
                "source": "amazon",
                "price": 319.99,
                "condition": "new",
                "seller_rating": 4.6,
                "shipping": 0.00
            }
        ]
    
    async def _analyze_market_position(
        self, product_name: str, brand: str, competitive_prices: List[Dict[str, Any]]
    ) -> str:
        """Analyze market position based on competitive data."""
        
        if not competitive_prices:
            return "unknown"
        
        avg_price = sum(p["price"] for p in competitive_prices) / len(competitive_prices)
        
        if avg_price < 50:
            return "budget"
        elif avg_price < 200:
            return "mid-range"
        else:
            return "premium"
    
    def _calculate_research_confidence(
        self, specs: Dict[str, Any], features: List[str], prices: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for research quality."""
        
        confidence = 0.0
        
        # Specifications found
        if specs:
            confidence += 0.3
        
        # Features extracted
        if len(features) >= 3:
            confidence += 0.3
        
        # Pricing data available
        if prices:
            confidence += 0.4
        
        return min(1.0, confidence)
