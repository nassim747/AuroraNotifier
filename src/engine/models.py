from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int] = None
    lat: float
    lon: float
    radius_km: int = 250
    threshold: int = 15
    fcm_token: str
    last_notified: Optional[datetime] = None
    created_at: Optional[datetime] = None
    active: bool = True


class AuroraAlert(BaseModel):
    user_id: int
    max_prob: float
    mean_prob: float
    cloud_coverage: float
    is_night: bool
    should_notify: bool
    timestamp: datetime