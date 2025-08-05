"""
Improved Shippo Service Wrapper
==============================

Enhanced Shippo service wrapper with better address validation and error handling.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from fs_agt_clean.services.logistics.shippo.shippo_service import ShippoService, ShippingDimensions, ShippingRate

logger = logging.getLogger(__name__)

class ImprovedShippoService:
    """Improved Shippo service with enhanced address validation."""
    
    def __init__(self, api_key: Optional[str] = None, test_mode: bool = True):
        """Initialize improved Shippo service."""
        self.api_key = api_key or os.getenv('SHIPPO_TEST_TOKEN', 'shippo_test_67adeff100d58f53d11d36053c4f02e6e75b3e5f')
        self.test_mode = test_mode
        
        # Initialize base service
        self.base_service = ShippoService(
            api_key=self.api_key,
            test_mode=test_mode
        )
        
        logger.info(f"Improved Shippo service initialized with key: {self.api_key[:20]}...")
    
    def validate_and_format_address(self, address: Dict[str, Any]) -> Dict[str, str]:
        """Enhanced address validation and formatting."""
        # Use base service validation
        validated = self.base_service._validate_shippo_address(address)
        
        # Additional validation
        required_fields = ['name', 'street1', 'city', 'state', 'zip', 'country']
        for field in required_fields:
            if field not in validated or not validated[field]:
                if field == 'name':
                    validated[field] = 'FlipSync Customer'
                elif field == 'country':
                    validated[field] = 'US'
                else:
                    raise ValueError(f"Missing required address field: {field}")
        
        # Ensure proper formatting
        validated['zip'] = str(validated['zip']).replace('-', '').strip()
        validated['state'] = str(validated['state']).upper().strip()
        validated['country'] = str(validated['country']).upper().strip()
        
        return validated
    
    async def calculate_rates_with_retry(
        self,
        dimensions: ShippingDimensions,
        from_address: Dict[str, Any],
        to_address: Dict[str, Any],
        max_retries: int = 3
    ) -> List[ShippingRate]:
        """Calculate shipping rates with retry logic and enhanced error handling."""
        
        # Validate addresses first
        try:
            validated_from = self.validate_and_format_address(from_address)
            validated_to = self.validate_and_format_address(to_address)
        except Exception as e:
            logger.error(f"Address validation failed: {e}")
            raise ValueError(f"Address validation failed: {e}")
        
        # Try rate calculation with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                rates = await self.base_service.calculate_shipping_rates(
                    dimensions=dimensions,
                    from_address=validated_from,
                    to_address=validated_to
                )
                
                if rates:
                    logger.info(f"Successfully calculated {len(rates)} rates on attempt {attempt + 1}")
                    return rates
                else:
                    logger.warning(f"No rates returned on attempt {attempt + 1}")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Rate calculation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
        
        # If all retries failed, raise the last error
        raise ValueError(f"Rate calculation failed after {max_retries} attempts: {last_error}")

# Global instance
_improved_shippo_service = None

def get_improved_shippo_service() -> ImprovedShippoService:
    """Get global improved Shippo service instance."""
    global _improved_shippo_service
    if _improved_shippo_service is None:
        _improved_shippo_service = ImprovedShippoService()
    return _improved_shippo_service
