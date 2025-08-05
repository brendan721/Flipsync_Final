#!/usr/bin/env python3
"""
Local Taxonomy Service for eBay category data.

This service loads and processes the EbayUsCatTaxonomy-2021.csv file to provide
instant category lookups without API calls.
"""

import csv
import logging
import time
from typing import Dict, Any, Optional, List, Set
import os

logger = logging.getLogger(__name__)


class LocalTaxonomyService:
    """Service for local eBay taxonomy data management."""

    def __init__(self, csv_file: str = "EbayUsCatTaxonomy-2021.csv"):
        """Initialize the local taxonomy service.

        Args:
            csv_file: Path to the eBay taxonomy CSV file
        """
        self.csv_file = csv_file
        self.category_map = {}  # category_id -> category_info
        self.department_map = {}  # department -> list of categories
        self.path_map = {}  # category_path -> category_id
        self.loaded = False
        self.load_time = None

        # Performance metrics
        self.metrics = {
            "total_categories": 0,
            "total_departments": 0,
            "load_time_ms": 0,
            "lookup_count": 0,
            "hit_count": 0,
        }

        # Load data on initialization
        self._load_taxonomy_data()

        logger.info(
            f"LocalTaxonomyService initialized with {self.metrics['total_categories']} categories"
        )

    def _load_taxonomy_data(self):
        """Load taxonomy data from CSV file."""
        if not os.path.exists(self.csv_file):
            logger.error(f"Taxonomy CSV file not found: {self.csv_file}")
            return

        start_time = time.perf_counter()

        try:
            # Try different encodings to handle the CSV file
            encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
            csv_data = None

            for encoding in encodings:
                try:
                    with open(self.csv_file, "r", encoding=encoding) as f:
                        csv_data = f.read()
                    logger.info(f"Successfully loaded CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue

            if csv_data is None:
                raise Exception("Could not decode CSV file with any supported encoding")

            # Parse the CSV data
            from io import StringIO

            csv_file_obj = StringIO(csv_data)
            with csv_file_obj as f:
                reader = csv.DictReader(f)

                departments = set()

                for row in reader:
                    department = row["DepartmentName"]
                    category_path = row["CategoryPath"]
                    category_id = row["CategoryValue"]

                    # Store category information
                    category_info = {
                        "category_id": category_id,
                        "department": department,
                        "category_path": category_path,
                        "specifics": self._generate_category_specifics(
                            department, category_path
                        ),
                        "source": "local_taxonomy",
                        "timestamp": time.time(),
                    }

                    self.category_map[category_id] = category_info
                    self.path_map[category_path] = category_id

                    # Track departments
                    departments.add(department)
                    if department not in self.department_map:
                        self.department_map[department] = []
                    self.department_map[department].append(category_id)

            # Update metrics
            end_time = time.perf_counter()
            self.metrics["total_categories"] = len(self.category_map)
            self.metrics["total_departments"] = len(departments)
            self.metrics["load_time_ms"] = (end_time - start_time) * 1000
            self.loaded = True
            self.load_time = time.time()

            logger.info(
                f"Loaded {self.metrics['total_categories']} categories in {self.metrics['load_time_ms']:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Failed to load taxonomy data: {e}")
            self.loaded = False

    def _generate_category_specifics(
        self, department: str, category_path: str
    ) -> Dict[str, Any]:
        """Generate item specifics based on department and category path.

        Args:
            department: eBay department name
            category_path: Full category path

        Returns:
            Dictionary of item specifics
        """
        # Base specifics that apply to most categories
        specifics = {
            "Brand": {"required": True, "values": []},
            "Condition": {"required": True, "values": ["New", "Used", "Refurbished"]},
            "Color": {"required": False, "values": []},
            "Material": {"required": False, "values": []},
        }

        # Department-specific enhancements
        if "Cell Phones" in category_path or "Smartphones" in category_path:
            specifics.update(
                {
                    "Model": {"required": True, "values": []},
                    "Storage Capacity": {
                        "required": False,
                        "values": ["64GB", "128GB", "256GB", "512GB", "1TB"],
                    },
                    "Network": {
                        "required": False,
                        "values": ["Unlocked", "Verizon", "AT&T", "T-Mobile", "Sprint"],
                    },
                    "Operating System": {
                        "required": False,
                        "values": ["iOS", "Android"],
                    },
                    "Screen Size": {
                        "required": False,
                        "values": ['Under 4"', '4" - 4.9"', '5" - 5.9"', '6" and over'],
                    },
                    "Camera Resolution": {
                        "required": False,
                        "values": [
                            "Under 8 MP",
                            "8-12 MP",
                            "13-16 MP",
                            "17 MP and over",
                        ],
                    },
                }
            )

        elif "Electronics" in department or "Consumer Electronics" in category_path:
            specifics.update(
                {
                    "Model": {"required": True, "values": []},
                    "Type": {"required": False, "values": []},
                    "Features": {"required": False, "values": []},
                    "Connectivity": {
                        "required": False,
                        "values": ["Wired", "Wireless", "Bluetooth", "Wi-Fi"],
                    },
                }
            )

        elif "Clothing" in department or "Fashion" in department:
            specifics.update(
                {
                    "Size": {
                        "required": True,
                        "values": ["XS", "S", "M", "L", "XL", "XXL"],
                    },
                    "Size Type": {
                        "required": False,
                        "values": ["Regular", "Petite", "Plus", "Tall"],
                    },
                    "Sleeve Length": {
                        "required": False,
                        "values": ["Short Sleeve", "Long Sleeve", "Sleeveless"],
                    },
                    "Fit": {
                        "required": False,
                        "values": ["Regular", "Slim", "Relaxed", "Oversized"],
                    },
                }
            )

        elif "Automotive" in department or "Motors" in department:
            specifics.update(
                {
                    "Make": {"required": True, "values": []},
                    "Model": {"required": True, "values": []},
                    "Year": {"required": True, "values": []},
                    "Part Number": {"required": False, "values": []},
                    "Fitment Type": {
                        "required": False,
                        "values": ["Direct Replacement", "Performance/Custom"],
                    },
                }
            )

        elif "Home" in department or "Garden" in department:
            specifics.update(
                {
                    "Room": {
                        "required": False,
                        "values": [
                            "Living Room",
                            "Bedroom",
                            "Kitchen",
                            "Bathroom",
                            "Dining Room",
                        ],
                    },
                    "Style": {
                        "required": False,
                        "values": ["Modern", "Traditional", "Contemporary", "Vintage"],
                    },
                    "Dimensions": {"required": False, "values": []},
                }
            )

        elif "Sports" in department or "Sporting Goods" in category_path:
            specifics.update(
                {
                    "Sport": {"required": False, "values": []},
                    "Size": {"required": False, "values": []},
                    "Gender": {"required": False, "values": ["Men", "Women", "Unisex"]},
                }
            )

        elif "Books" in department or "Media" in department:
            specifics.update(
                {
                    "Format": {
                        "required": True,
                        "values": ["Hardcover", "Paperback", "Digital", "Audio"],
                    },
                    "Language": {
                        "required": False,
                        "values": ["English", "Spanish", "French", "German"],
                    },
                    "Publication Year": {"required": False, "values": []},
                    "Genre": {"required": False, "values": []},
                }
            )

        elif "Toys" in department or "Hobbies" in department:
            specifics.update(
                {
                    "Age Level": {
                        "required": False,
                        "values": [
                            "0-2 years",
                            "3-4 years",
                            "5-7 years",
                            "8-11 years",
                            "12+ years",
                        ],
                    },
                    "Character Family": {"required": False, "values": []},
                    "Type": {"required": False, "values": []},
                }
            )

        return specifics

    def get_category_info(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category information by category ID.

        Args:
            category_id: eBay category ID

        Returns:
            Category information dictionary or None if not found
        """
        self.metrics["lookup_count"] += 1

        if not self.loaded:
            logger.warning("Taxonomy data not loaded")
            return None

        category_info = self.category_map.get(category_id)
        if category_info:
            self.metrics["hit_count"] += 1
            logger.debug(f"Found local taxonomy data for category {category_id}")
            return category_info.copy()  # Return a copy to prevent modification

        logger.debug(f"No local taxonomy data found for category {category_id}")
        return None

    def search_categories(
        self, search_term: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search categories by name or path.

        Args:
            search_term: Search term to match against category paths
            limit: Maximum number of results to return

        Returns:
            List of matching category information dictionaries
        """
        if not self.loaded:
            return []

        search_term_lower = search_term.lower()
        results = []

        for category_info in self.category_map.values():
            if (
                search_term_lower in category_info["category_path"].lower()
                or search_term_lower in category_info["department"].lower()
            ):
                results.append(category_info.copy())

                if len(results) >= limit:
                    break

        return results

    def get_department_categories(self, department: str) -> List[str]:
        """Get all category IDs for a department.

        Args:
            department: Department name

        Returns:
            List of category IDs
        """
        if not self.loaded:
            return []

        return self.department_map.get(department, [])

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics.

        Returns:
            Dictionary of service metrics
        """
        hit_rate = 0.0
        if self.metrics["lookup_count"] > 0:
            hit_rate = (self.metrics["hit_count"] / self.metrics["lookup_count"]) * 100

        return {
            **self.metrics,
            "hit_rate_percentage": hit_rate,
            "loaded": self.loaded,
            "load_timestamp": self.load_time,
        }

    def is_data_fresh(
        self, category_info: Dict[str, Any], max_age_hours: int = 24
    ) -> bool:
        """Check if category data is fresh enough.

        Args:
            category_info: Category information dictionary
            max_age_hours: Maximum age in hours

        Returns:
            True if data is fresh, False otherwise
        """
        if not category_info or "timestamp" not in category_info:
            return False

        age_seconds = time.time() - category_info["timestamp"]
        age_hours = age_seconds / 3600

        return age_hours <= max_age_hours

    def reload_data(self):
        """Reload taxonomy data from CSV file."""
        logger.info("Reloading taxonomy data...")
        self.category_map.clear()
        self.department_map.clear()
        self.path_map.clear()
        self.loaded = False
        self._load_taxonomy_data()


# Global instance for easy access
_local_taxonomy_service = None


def get_local_taxonomy_service(
    csv_file: str = "EbayUsCatTaxonomy-2021.csv",
) -> LocalTaxonomyService:
    """Get global local taxonomy service instance.

    Args:
        csv_file: Path to the eBay taxonomy CSV file

    Returns:
        LocalTaxonomyService instance
    """
    global _local_taxonomy_service

    if _local_taxonomy_service is None:
        _local_taxonomy_service = LocalTaxonomyService(csv_file)

    return _local_taxonomy_service
