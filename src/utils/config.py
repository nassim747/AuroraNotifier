import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openweather_key: str
    fcm_server_key: str
    database_url: str = "sqlite:///data/aurora_alert.db"
    
    radius_km: int = 250
    prob_threshold: int = 15
    cloud_max: int = 40
    cooldown_h: int = 3
    
    check_interval_min: int = 5
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()