"""
Cloud Vision Service for FlipSync - Strategic Cloud API Integration
=================================================================

Provides cost-optimized cloud vision API integration for complex cases.
Routes to the most cost-effective API based on quotas and requirements.
Used only when local analysis (barcode/OCR) fails to provide sufficient confidence.

Features:
- Amazon Rekognition integration for object/text detection
- Google Cloud Vision as fallback option
- Smart routing based on cost and quotas
- Rate limiting and quota management
- Comprehensive error handling
- Cost tracking and optimization
"""

import io
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from PIL import Image

# Cloud vision APIs
try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    REKOGNITION_AVAILABLE = True
except ImportError:
    REKOGNITION_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    BotoCoreError = Exception

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    vision = None
    google_exceptions = None

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud vision providers."""
    
    AMAZON_REKOGNITION = "amazon_rekognition"
    GOOGLE_VISION = "google_vision"
    AUTO_SELECT = "auto_select"


@dataclass
class VisionResult:
    """Result from cloud vision analysis."""
    
    labels: List[str]
    text_detections: List[str]
    confidence: float
    provider: CloudProvider
    processing_time_ms: float
    cost_estimate: float
    quota_used: int = 1


@dataclass
class ProviderQuota:
    """Quota tracking for cloud providers."""
    
    daily_limit: int
    current_usage: int
    cost_per_request: float
    reset_time: float


class CloudVisionService:
    """Cost-optimized cloud vision API integration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize cloud vision service."""
        self.config = config or {}
        
        # Provider configuration
        self.aws_region = self.config.get("aws_region", "us-east-1")
        self.google_project_id = self.config.get("google_project_id")
        
        # Cost optimization settings
        self.max_cost_per_request = self.config.get("max_cost_per_request", 0.01)
        self.prefer_cheaper_provider = self.config.get("prefer_cheaper_provider", True)
        
        # Initialize clients
        self.rekognition_client = None
        self.google_client = None
        
        # Quota tracking
        self.quotas = {
            CloudProvider.AMAZON_REKOGNITION: ProviderQuota(
                daily_limit=1000,
                current_usage=0,
                cost_per_request=0.001,  # $0.001 per image
                reset_time=time.time() + 86400  # 24 hours
            ),
            CloudProvider.GOOGLE_VISION: ProviderQuota(
                daily_limit=1000,
                current_usage=0,
                cost_per_request=0.0015,  # $0.0015 per image
                reset_time=time.time() + 86400
            )
        }
        
        # Performance tracking
        self.stats = {
            "total_requests": 0,
            "rekognition_requests": 0,
            "google_vision_requests": 0,
            "total_cost": 0.0,
            "average_processing_time": 0.0,
            "error_count": 0,
        }
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize cloud API clients."""
        # Initialize Amazon Rekognition
        if REKOGNITION_AVAILABLE:
            try:
                self.rekognition_client = boto3.client(
                    'rekognition',
                    region_name=self.aws_region
                )
                logger.info("Amazon Rekognition client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Rekognition client: {e}")
        
        # Initialize Google Vision
        if GOOGLE_VISION_AVAILABLE and self.google_project_id:
            try:
                self.google_client = vision.ImageAnnotatorClient()
                logger.info("Google Vision client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Vision client: {e}")
    
    async def analyze_with_rekognition(self, image: Image.Image) -> VisionResult:
        """
        Use Amazon Rekognition for object/text detection.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            VisionResult with analysis results
        """
        start_time = time.perf_counter()
        
        if not self.rekognition_client:
            raise RuntimeError("Amazon Rekognition client not available")
        
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            # Detect labels (objects)
            labels_response = self.rekognition_client.detect_labels(
                Image={'Bytes': img_bytes},
                MaxLabels=10,
                MinConfidence=70
            )
            
            # Detect text
            text_response = self.rekognition_client.detect_text(
                Image={'Bytes': img_bytes}
            )
            
            # Process results
            labels = [
                label['Name'] for label in labels_response['Labels']
                if label['Confidence'] > 70
            ]
            
            text_detections = [
                detection['DetectedText'] 
                for detection in text_response['TextDetections']
                if detection['Type'] == 'LINE' and detection['Confidence'] > 70
            ]
            
            # Calculate confidence (average of label confidences)
            if labels_response['Labels']:
                avg_confidence = sum(
                    label['Confidence'] for label in labels_response['Labels']
                ) / len(labels_response['Labels']) / 100.0
            else:
                avg_confidence = 0.5
            
            processing_time = (time.perf_counter() - start_time) * 1000
            cost_estimate = self.quotas[CloudProvider.AMAZON_REKOGNITION].cost_per_request
            
            # Update stats
            self.stats["rekognition_requests"] += 1
            self.quotas[CloudProvider.AMAZON_REKOGNITION].current_usage += 1
            
            logger.debug(
                f"Rekognition analysis: {len(labels)} labels, {len(text_detections)} text items"
            )
            
            return VisionResult(
                labels=labels,
                text_detections=text_detections,
                confidence=avg_confidence,
                provider=CloudProvider.AMAZON_REKOGNITION,
                processing_time_ms=processing_time,
                cost_estimate=cost_estimate
            )
            
        except (ClientError, BotoCoreError) as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Rekognition analysis failed: {e}")
            self.stats["error_count"] += 1
            raise RuntimeError(f"Rekognition analysis failed: {str(e)}")
    
    async def analyze_with_google_vision(self, image: Image.Image) -> VisionResult:
        """
        Fallback to Google Cloud Vision.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            VisionResult with analysis results
        """
        start_time = time.perf_counter()
        
        if not self.google_client:
            raise RuntimeError("Google Vision client not available")
        
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            # Create vision image object
            vision_image = vision.Image(content=img_bytes)
            
            # Detect labels
            labels_response = self.google_client.label_detection(image=vision_image)
            
            # Detect text
            text_response = self.google_client.text_detection(image=vision_image)
            
            # Process results
            labels = [
                label.description for label in labels_response.label_annotations
                if label.score > 0.7
            ]
            
            text_detections = []
            if text_response.text_annotations:
                # First annotation contains full text, others are individual words
                full_text = text_response.text_annotations[0].description
                text_detections = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            # Calculate confidence
            if labels_response.label_annotations:
                avg_confidence = sum(
                    label.score for label in labels_response.label_annotations
                ) / len(labels_response.label_annotations)
            else:
                avg_confidence = 0.5
            
            processing_time = (time.perf_counter() - start_time) * 1000
            cost_estimate = self.quotas[CloudProvider.GOOGLE_VISION].cost_per_request
            
            # Update stats
            self.stats["google_vision_requests"] += 1
            self.quotas[CloudProvider.GOOGLE_VISION].current_usage += 1
            
            logger.debug(
                f"Google Vision analysis: {len(labels)} labels, {len(text_detections)} text items"
            )
            
            return VisionResult(
                labels=labels,
                text_detections=text_detections,
                confidence=avg_confidence,
                provider=CloudProvider.GOOGLE_VISION,
                processing_time_ms=processing_time,
                cost_estimate=cost_estimate
            )
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Google Vision analysis failed: {e}")
            self.stats["error_count"] += 1
            raise RuntimeError(f"Google Vision analysis failed: {str(e)}")
    
    async def get_cheapest_analysis(self, image: Image.Image) -> VisionResult:
        """
        Route to most cost-effective API based on quotas.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            VisionResult from the selected provider
        """
        start_time = time.perf_counter()
        self.stats["total_requests"] += 1
        
        try:
            # Select best provider based on cost and availability
            provider = self._select_optimal_provider()
            
            if provider == CloudProvider.AMAZON_REKOGNITION:
                result = await self.analyze_with_rekognition(image)
            elif provider == CloudProvider.GOOGLE_VISION:
                result = await self.analyze_with_google_vision(image)
            else:
                raise RuntimeError("No cloud vision providers available")
            
            # Update cost tracking
            self.stats["total_cost"] += result.cost_estimate
            
            # Update average processing time
            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_average_processing_time(processing_time)
            
            logger.info(
                f"Cloud vision analysis completed with {provider.value} "
                f"(cost: ${result.cost_estimate:.4f}, time: {processing_time:.1f}ms)"
            )
            
            return result
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Cloud vision analysis failed: {e}")
            self.stats["error_count"] += 1
            self._update_average_processing_time(processing_time)
            raise
    
    def _select_optimal_provider(self) -> CloudProvider:
        """Select the most cost-effective available provider."""
        available_providers = []
        
        # Check Rekognition availability
        if (self.rekognition_client and 
            self.quotas[CloudProvider.AMAZON_REKOGNITION].current_usage < 
            self.quotas[CloudProvider.AMAZON_REKOGNITION].daily_limit):
            available_providers.append(CloudProvider.AMAZON_REKOGNITION)
        
        # Check Google Vision availability
        if (self.google_client and 
            self.quotas[CloudProvider.GOOGLE_VISION].current_usage < 
            self.quotas[CloudProvider.GOOGLE_VISION].daily_limit):
            available_providers.append(CloudProvider.GOOGLE_VISION)
        
        if not available_providers:
            raise RuntimeError("No cloud vision providers available or quota exceeded")
        
        # Select cheapest provider
        if self.prefer_cheaper_provider:
            costs = {
                provider: self.quotas[provider].cost_per_request 
                for provider in available_providers
            }
            return min(costs.keys(), key=lambda p: costs[p])
        else:
            # Return first available
            return available_providers[0]
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time statistics."""
        total = self.stats["total_requests"]
        current_avg = self.stats["average_processing_time"]
        new_avg = ((current_avg * (total - 1)) + processing_time) / total
        self.stats["average_processing_time"] = new_avg
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cloud vision service statistics."""
        return {
            **self.stats,
            "quotas": {
                provider.value: {
                    "daily_limit": quota.daily_limit,
                    "current_usage": quota.current_usage,
                    "usage_percentage": (quota.current_usage / quota.daily_limit) * 100,
                    "cost_per_request": quota.cost_per_request,
                }
                for provider, quota in self.quotas.items()
            },
            "providers_available": {
                "rekognition": self.rekognition_client is not None,
                "google_vision": self.google_client is not None,
            },
            "cost_savings_vs_always_cloud": self._calculate_cost_savings(),
        }
    
    def _calculate_cost_savings(self) -> float:
        """Calculate cost savings vs always using cloud vision."""
        if self.stats["total_requests"] == 0:
            return 0.0
        
        # Estimate cost if all requests went to cloud
        avg_cloud_cost = (
            self.quotas[CloudProvider.AMAZON_REKOGNITION].cost_per_request +
            self.quotas[CloudProvider.GOOGLE_VISION].cost_per_request
        ) / 2
        
        estimated_full_cloud_cost = self.stats["total_requests"] * avg_cloud_cost
        actual_cost = self.stats["total_cost"]
        
        if estimated_full_cloud_cost > 0:
            savings = (estimated_full_cloud_cost - actual_cost) / estimated_full_cloud_cost
            return max(0.0, savings)
        
        return 0.0
