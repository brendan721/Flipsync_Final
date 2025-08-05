"""Metrics export functionality."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.monitoring.models import MetricDataPoint

logger = logging.getLogger(__name__)


class MetricsExporter:
    """Exports metrics to various formats and destinations."""

    def __init__(self):
        """Initialize metrics exporter."""
        self._last_export: Optional[datetime] = None
        self._ready = True  # Initialize as ready
        self.export_formats = ["json"]  # Default to JSON format
        self.export_destinations = ["file"]  # Default to file export

    async def export_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Export metrics to configured destinations.

        Args:
            metrics: Metrics to export

        Returns:
            bool: True if export successful
        """
        try:
            self._last_export = datetime.now()
            # Convert to standard format
            metric_points = self._convert_to_data_points(metrics)

            # Export to configured destinations
            await self._export_to_json(metric_points)

            return True
        except Exception as e:
            logger.error("Error exporting metrics: %s", e)
            self._ready = False  # Mark as not ready on error
            return False

    def _convert_to_data_points(self, metrics: Dict[str, Any]) -> List[MetricDataPoint]:
        """Convert raw metrics to standard data points."""
        data_points = []
        timestamp = datetime.now()

        for name, value in metrics.items():
            if isinstance(value, dict):
                for subname, subvalue in value.items():
                    if isinstance(subvalue, (int, float)):
                        data_points.append(
                            MetricDataPoint(
                                name=f"{name}_{subname}",
                                value=float(subvalue),
                                timestamp=timestamp,
                                labels={"category": name},
                            )
                        )
            elif isinstance(value, (int, float)):
                data_points.append(
                    MetricDataPoint(
                        name=name, value=float(value), timestamp=timestamp, labels={}
                    )
                )
        return data_points

    async def _export_to_json(self, metrics: List[MetricDataPoint]) -> None:
        """Export metrics to JSON format."""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "labels": m.labels,
                    }
                    for m in metrics
                ],
            }
            # TODO: Configure output path
            with open("metrics_export.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Error exporting to JSON: %s", e)
            self._ready = False  # Mark as not ready on error
            raise

    async def cleanup(self):
        """Cleanup resources."""
        self._last_export = None
        self._ready = True  # Reset ready state
        return {"status": "cleaned up", "timestamp": datetime.now()}

    async def is_ready(self) -> bool:
        """Check if the exporter is ready for production use.

        Returns:
            bool: True if the exporter is ready for production use
        """
        return (
            self._ready and bool(self.export_formats) and bool(self.export_destinations)
        )


class ExportService:
    """Service for exporting FlipSync data in various formats."""

    def __init__(self):
        """Initialize the export service."""
        self.supported_formats = ["json", "csv", "xml"]
        self.export_history: List[Dict[str, Any]] = []

    async def export_data(self, data: Any, format_type: str = "json") -> str:
        """Export data in the specified format.

        Args:
            data: Data to export
            format_type: Export format (json, csv, xml)

        Returns:
            Exported data as string
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
            export_record["size"] = len(result)
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
