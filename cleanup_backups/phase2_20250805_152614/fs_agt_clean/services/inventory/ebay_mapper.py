"""eBay inventory data mapping service."""

import logging
import aiohttp
import aiofiles
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pathlib import Path

logger = logging.getLogger(__name__)


class EbayInventoryMapper:
    """Maps eBay inventory data to FlipSync InventoryItem format."""

    def __init__(self, storage_base_path: str = "/opt/flipsync/storage/inventory"):
        self.logger = logger
        self.storage_base_path = Path(storage_base_path)
        self.storage_base_path.mkdir(parents=True, exist_ok=True)

        # Image processing settings
        self.max_image_size = 1024 * 1024  # 1MB max for main image
        self.supported_formats = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def map_ebay_inventory_to_flipsync(
        self, ebay_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Map eBay inventory items to FlipSync InventoryItem format.

        Args:
            ebay_items: List of eBay inventory items from API

        Returns:
            List of mapped inventory items for FlipSync database
        """
        mapped_items = []

        for item in ebay_items:
            try:
                mapped_item = await self._map_single_item_async(item)
                if mapped_item:
                    mapped_items.append(mapped_item)
            except Exception as e:
                sku = item.get("sku", "unknown")
                self.logger.error(f"Error mapping eBay item {sku}: {str(e)}")
                continue

        return mapped_items

    async def _map_single_item_async(
        self, ebay_item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Map a single eBay inventory item to FlipSync format with image download.

        Args:
            ebay_item: Single eBay inventory item from API

        Returns:
            Mapped inventory item or None if mapping fails
        """
        try:
            # Extract basic fields
            sku = ebay_item.get("sku")
            if not sku:
                self.logger.warning("eBay item missing SKU, skipping")
                return None

            product = ebay_item.get("product", {})
            availability = ebay_item.get("availability", {})
            ship_availability = availability.get("shipToLocationAvailability", {})

            # Extract pricing from offers (eBay stores pricing in offers)
            price = self._extract_price(ebay_item)

            # Extract weight and dimensions
            weight, dimensions = self._extract_package_info(ebay_item)

            # Extract barcode (UPC/EAN)
            barcode = self._extract_barcode(product)

            # Download and store main image
            image_urls = product.get("imageUrls", [])
            image_info = await self.download_and_store_main_image(sku, image_urls)

            # Create metadata JSON with eBay-specific data including images
            metadata = self._create_metadata_with_images(ebay_item, image_info)

            # Map to FlipSync InventoryItem format
            mapped_item = {
                "sku": sku,
                "name": product.get("title", ""),
                "description": product.get("description", ""),
                "category": self._extract_category(ebay_item),
                "quantity": ship_availability.get("quantity", 0),
                "price": price,
                "weight": weight,
                "dimensions": dimensions,
                "barcode": barcode,
                "condition_ebay": ebay_item.get("condition"),
                "marketplace_source": "eBay",
                "metadata_json": metadata,
                "last_sync_at": datetime.utcnow(),
                "is_active": True,
            }

            return mapped_item

        except Exception as e:
            self.logger.error(f"Error in _map_single_item_async: {str(e)}")
            return None

    def _map_single_item(self, ebay_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map a single eBay inventory item to FlipSync format.

        Args:
            ebay_item: Single eBay inventory item from API

        Returns:
            Mapped inventory item or None if mapping fails
        """
        try:
            # Extract basic fields
            sku = ebay_item.get("sku")
            if not sku:
                self.logger.warning("eBay item missing SKU, skipping")
                return None

            product = ebay_item.get("product", {})
            availability = ebay_item.get("availability", {})
            ship_availability = availability.get("shipToLocationAvailability", {})

            # Extract pricing from offers (eBay stores pricing in offers)
            price = self._extract_price(ebay_item)

            # Extract weight and dimensions
            weight, dimensions = self._extract_package_info(ebay_item)

            # Extract barcode (UPC/EAN)
            barcode = self._extract_barcode(product)

            # Create metadata JSON with eBay-specific data
            metadata = self._create_metadata(ebay_item)

            # Map to FlipSync InventoryItem format
            mapped_item = {
                "sku": sku,
                "name": product.get("title", ""),
                "description": product.get("description", ""),
                "category": self._extract_category(ebay_item),
                "quantity": ship_availability.get("quantity", 0),
                "price": price,
                "weight": weight,
                "dimensions": dimensions,
                "barcode": barcode,
                "condition_ebay": ebay_item.get("condition"),
                "marketplace_source": "eBay",
                "metadata_json": metadata,
                "last_sync_at": datetime.utcnow(),
                "is_active": True,
            }

            return mapped_item

        except Exception as e:
            self.logger.error(f"Error in _map_single_item: {str(e)}")
            return None

    def _extract_price(self, ebay_item: Dict[str, Any]) -> Optional[Decimal]:
        """Extract price from eBay item (from offers structure)."""
        try:
            # eBay stores pricing in offers array
            offers = ebay_item.get("offers", [])
            if offers and len(offers) > 0:
                price_info = offers[0].get("price", {})
                price_value = price_info.get("value")
                if price_value is not None:
                    return Decimal(str(price_value))

            # Fallback: check if price is directly in the item
            if "price" in ebay_item:
                return Decimal(str(ebay_item["price"]))

            return None
        except (ValueError, TypeError, KeyError):
            return None

    def _extract_package_info(self, ebay_item: Dict[str, Any]) -> tuple:
        """Extract weight and dimensions from eBay package info."""
        try:
            package_info = ebay_item.get("packageWeightAndSize", {})

            # Extract weight
            weight = None
            weight_info = package_info.get("weight", {})
            if weight_info:
                weight_value = weight_info.get("value")
                weight_unit = weight_info.get("unit", "").upper()
                if weight_value:
                    # Convert to standard unit (pounds)
                    if weight_unit == "KILOGRAM":
                        weight = Decimal(str(weight_value)) * Decimal("2.20462")
                    elif weight_unit in ["POUND", "LB"]:
                        weight = Decimal(str(weight_value))
                    elif weight_unit == "OUNCE":
                        weight = Decimal(str(weight_value)) / Decimal("16")

            # Extract dimensions
            dimensions = None
            dim_info = package_info.get("dimensions", {})
            if dim_info:
                length = dim_info.get("length")
                width = dim_info.get("width")
                height = dim_info.get("height")
                unit = dim_info.get("unit", "").upper()

                if all([length, width, height]):
                    # Convert to standard format (inches)
                    if unit == "CENTIMETER":
                        length = float(length) / 2.54
                        width = float(width) / 2.54
                        height = float(height) / 2.54

                    dimensions = f"{length:.1f}x{width:.1f}x{height:.1f}"

            return weight, dimensions

        except (ValueError, TypeError, KeyError):
            return None, None

    def _extract_barcode(self, product: Dict[str, Any]) -> Optional[str]:
        """Extract barcode (UPC/EAN) from eBay product data."""
        try:
            # Check UPC first
            upc_list = product.get("upc", [])
            if upc_list and len(upc_list) > 0:
                return upc_list[0]

            # Check EAN
            ean_list = product.get("ean", [])
            if ean_list and len(ean_list) > 0:
                return ean_list[0]

            # Check ISBN for books
            isbn_list = product.get("isbn", [])
            if isbn_list and len(isbn_list) > 0:
                return isbn_list[0]

            return None
        except (TypeError, KeyError):
            return None

    def _extract_category(self, ebay_item: Dict[str, Any]) -> Optional[str]:
        """Extract category information from eBay item."""
        try:
            # eBay category information might be in different places
            # This is a placeholder - actual implementation depends on eBay response structure
            return ebay_item.get("categoryId") or ebay_item.get("category")
        except (TypeError, KeyError):
            return None

    def _create_metadata(self, ebay_item: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata JSON with eBay-specific data."""
        try:
            product = ebay_item.get("product", {})

            metadata = {
                "ebay_data": {
                    "item_specifics": product.get("aspects", {}),
                    "brand": product.get("brand"),
                    "mpn": product.get("mpn"),
                    "epid": product.get("epid"),
                    "images": product.get("imageUrls", []),
                    "video_ids": product.get("videoIds", []),
                    "subtitle": product.get("subtitle"),
                    "condition_description": ebay_item.get("conditionDescription"),
                    "condition_descriptors": ebay_item.get("conditionDescriptors", []),
                },
                "availability": {
                    "pickup_locations": ebay_item.get("availability", {}).get(
                        "pickupAtLocationAvailability", []
                    ),
                    "fulfillment_time": self._extract_fulfillment_time(ebay_item),
                },
                "shipping": self._extract_shipping_info(ebay_item),
                "sync_info": {
                    "last_sync": datetime.utcnow().isoformat(),
                    "source": "eBay Inventory API",
                },
            }

            return metadata

        except Exception as e:
            self.logger.error(f"Error creating metadata: {str(e)}")
            return {}

    def _extract_fulfillment_time(self, ebay_item: Dict[str, Any]) -> Optional[Dict]:
        """Extract fulfillment time information."""
        try:
            availability = ebay_item.get("availability", {})
            ship_availability = availability.get("shipToLocationAvailability", {})
            distributions = ship_availability.get("availabilityDistributions", [])

            if distributions and len(distributions) > 0:
                fulfillment = distributions[0].get("fulfillmentTime", {})
                if fulfillment:
                    return {
                        "value": fulfillment.get("value"),
                        "unit": fulfillment.get("unit"),
                    }
            return None
        except (TypeError, KeyError):
            return None

    def _extract_shipping_info(self, ebay_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract shipping information from eBay item."""
        try:
            # Placeholder for shipping information extraction
            # Actual implementation depends on eBay response structure
            package_info = ebay_item.get("packageWeightAndSize", {})

            shipping_info = {
                "package_type": package_info.get("packageType"),
                "shipping_irregular": package_info.get("shippingIrregular", False),
                "weight": package_info.get("weight", {}),
                "dimensions": package_info.get("dimensions", {}),
            }

            return shipping_info

        except Exception as e:
            self.logger.error(f"Error extracting shipping info: {str(e)}")
            return {}

    async def download_and_store_main_image(
        self, sku: str, image_urls: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Download and store the main product image locally.

        Args:
            sku: Product SKU for file naming
            image_urls: List of image URLs from eBay

        Returns:
            Dictionary with image storage information or None if failed
        """
        if not image_urls:
            return None

        main_image_url = image_urls[0]  # Use first image as main

        try:
            # Create SKU directory
            sku_dir = self.storage_base_path / sku
            sku_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with hash for uniqueness
            url_hash = hashlib.md5(main_image_url.encode()).hexdigest()[:8]
            parsed_url = urlparse(main_image_url)
            original_ext = Path(parsed_url.path).suffix.lower()

            if original_ext not in self.supported_formats:
                original_ext = ".jpg"  # Default to JPEG

            filename = f"main_{url_hash}{original_ext}"
            file_path = sku_dir / filename

            # Skip download if file already exists
            if file_path.exists():
                file_size = file_path.stat().st_size
                return {
                    "main_image_url": f"/storage/inventory/{sku}/{filename}",
                    "main_image_path": str(file_path),
                    "file_size": file_size,
                    "format": original_ext[1:].upper(),
                    "download_date": datetime.utcnow().isoformat(),
                    "source_url": main_image_url,
                    "status": "cached",
                }

            # Download image
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(main_image_url) as response:
                    if response.status != 200:
                        self.logger.warning(
                            f"Failed to download image for {sku}: HTTP {response.status}"
                        )
                        return None

                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > self.max_image_size:
                        self.logger.warning(
                            f"Image too large for {sku}: {content_length} bytes"
                        )
                        return None

                    # Read and save image data
                    image_data = await response.read()

                    if len(image_data) > self.max_image_size:
                        self.logger.warning(
                            f"Downloaded image too large for {sku}: {len(image_data)} bytes"
                        )
                        return None

                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(image_data)

                    self.logger.info(
                        f"Downloaded main image for {sku}: {len(image_data)} bytes"
                    )

                    return {
                        "main_image_url": f"/storage/inventory/{sku}/{filename}",
                        "main_image_path": str(file_path),
                        "file_size": len(image_data),
                        "format": original_ext[1:].upper(),
                        "download_date": datetime.utcnow().isoformat(),
                        "source_url": main_image_url,
                        "status": "downloaded",
                    }

        except Exception as e:
            self.logger.error(f"Error downloading image for {sku}: {str(e)}")
            return None

    def _create_metadata_with_images(
        self, ebay_item: Dict[str, Any], image_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create metadata JSON with eBay-specific data including image information."""
        try:
            product = ebay_item.get("product", {})

            # Start with base metadata
            metadata = self._create_metadata(ebay_item)

            # Add enhanced image information
            if image_info:
                metadata["images"] = {
                    "main_image": image_info,
                    "additional_images": product.get("imageUrls", [])[
                        1:
                    ],  # Skip first (main) image
                    "total_images": len(product.get("imageUrls", [])),
                    "has_local_main": True,
                }
            else:
                # Fallback to eBay URLs only
                image_urls = product.get("imageUrls", [])
                metadata["images"] = {
                    "main_image": {"source_url": image_urls[0]} if image_urls else None,
                    "additional_images": image_urls[1:] if len(image_urls) > 1 else [],
                    "total_images": len(image_urls),
                    "has_local_main": False,
                }

            return metadata

        except Exception as e:
            self.logger.error(f"Error creating metadata with images: {str(e)}")
            return self._create_metadata(ebay_item)  # Fallback to basic metadata
