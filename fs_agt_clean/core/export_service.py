"""Export service for FlipSync data export functionality."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting FlipSync data in various formats."""

    def __init__(self):
        """Initialize the export service."""
        self.supported_formats = ["json", "csv", "xml"]
        self.export_history: List[Dict[str, Any]] = []

    async def export_data(
        self, data: Any, format_type: str = "json"
    ) -> Union[str, bytes]:
        """Export data in the specified format.

        Args:
            data: Data to export
            format_type: Export format (json, csv, xml)

        Returns:
            Exported data as string or bytes
        """
        try:
            if format_type.lower() not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")

            # Record export attempt
            export_record = {
                "timestamp": datetime.now().isoformat(),
                "format": format_type,
                "data_type": type(data).__name__,
                "status": "started",
            }

            if format_type.lower() == "json":
                result = await self._export_json(data)
            elif format_type.lower() == "csv":
                result = await self._export_csv(data)
            elif format_type.lower() == "xml":
                result = await self._export_xml(data)
            else:
                raise ValueError(f"Format {format_type} not implemented")

            export_record["status"] = "completed"
            export_record["size"] = (
                len(result) if isinstance(result, str) else len(result)
            )
            self.export_history.append(export_record)

            return result

        except Exception as e:
            logger.error(f"Export failed: {e}")
            export_record["status"] = "failed"
            export_record["error"] = str(e)
            self.export_history.append(export_record)
            raise

    async def _export_json(self, data: Any) -> str:
        """Export data as JSON."""
        try:
            # Handle different data types
            if hasattr(data, "__dict__"):
                # Convert objects to dict
                data = data.__dict__
            elif hasattr(data, "_asdict"):
                # Handle namedtuples
                data = data._asdict()

            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise

    async def _export_csv(self, data: Any) -> str:
        """Export data as CSV."""
        try:
            import csv
            import io

            output = io.StringIO()

            if isinstance(data, list) and len(data) > 0:
                # Handle list of dictionaries
                if isinstance(data[0], dict):
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    # Handle list of values
                    writer = csv.writer(output)
                    for item in data:
                        writer.writerow([item])
            elif isinstance(data, dict):
                # Handle single dictionary
                writer = csv.DictWriter(output, fieldnames=data.keys())
                writer.writeheader()
                writer.writerow(data)
            else:
                # Handle single value
                writer = csv.writer(output)
                writer.writerow([data])

            return output.getvalue()
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise

    async def _export_xml(self, data: Any) -> str:
        """Export data as XML."""
        try:
            import xml.etree.ElementTree as ET

            root = ET.Element("export")
            root.set("timestamp", datetime.now().isoformat())

            def add_element(parent, key, value):
                elem = ET.SubElement(parent, str(key))
                if isinstance(value, dict):
                    for k, v in value.items():
                        add_element(elem, k, v)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        add_element(elem, f"item_{i}", item)
                else:
                    elem.text = str(value)

            if isinstance(data, dict):
                for key, value in data.items():
                    add_element(root, key, value)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    add_element(root, f"item_{i}", item)
            else:
                elem = ET.SubElement(root, "data")
                elem.text = str(data)

            return ET.tostring(root, encoding="unicode")
        except Exception as e:
            logger.error(f"XML export failed: {e}")
            raise

    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get the export history."""
        return self.export_history.copy()

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return self.supported_formats.copy()

    async def clear_history(self) -> None:
        """Clear the export history."""
        self.export_history.clear()

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the export service."""
        try:
            # Test basic functionality
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            await self.export_data(test_data, "json")

            return {
                "status": "healthy",
                "supported_formats": self.supported_formats,
                "export_count": len(self.export_history),
                "last_export": self.export_history[-1] if self.export_history else None,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "supported_formats": self.supported_formats,
                "export_count": len(self.export_history),
            }
