"""
eBay Service compatibility module.

This module provides backward compatibility for imports that expect
the EbayService to be in fs_agt_clean.services.marketplace.ebay_service.
"""

# Import from the actual location
from fs_agt_clean.services.marketplace.ebay.service import *
