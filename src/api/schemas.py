from pydantic import BaseModel, Field
from typing import Optional


class SubscribeRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude") 
    radius_km: int = Field(250, ge=50, le=1000, description="Search radius in kilometers")
    threshold: int = Field(15, ge=1, le=100, description="Aurora probability threshold percentage")
    token: str = Field(..., description="FCM device token")


class UpdatePreferencesRequest(BaseModel):
    radius_km: Optional[int] = Field(None, ge=50, le=1000, description="Search radius in kilometers")
    threshold: Optional[int] = Field(None, ge=1, le=100, description="Aurora probability threshold percentage")


class UnsubscribeRequest(BaseModel):
    token: str = Field(..., description="FCM device token")


class StatusResponse(BaseModel):
    status: str
    message: str
    active_users: Optional[int] = None


class SubscribeResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[int] = None