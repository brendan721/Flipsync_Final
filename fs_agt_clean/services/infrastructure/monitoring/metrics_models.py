from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

"\nData models for the metrics service\n"


class MetricFilter(BaseModel):
    endpoints: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class WSConnection(BaseModel):
    client_id: str
    filters: Optional[MetricFilter] = None
    last_active: datetime = Field(default_factory=datetime.now)


class MetricUpdate(BaseModel):
    timestamp: datetime
    metric_type: str
    value: Union[float, Dict[str, float]]
    labels: Dict[str, str]
    source: str


class ClientConfig(BaseModel):
    update_interval: int = 5
    batch_size: int = 100
    enabled_metrics: List[str] = []
    alert_preferences: Dict[str, bool] = {}
