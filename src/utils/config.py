import os
import json
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openweather_key: str
    fcm_service_account_json: str
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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Handle multiline JSON in .env file manually
        self._load_multiline_json()
    
    def _load_multiline_json(self):
        """Load multiline JSON from .env file manually."""
        env_path = Path(".env")
        if not env_path.exists():
            return
        
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Find and parse the JSON
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith('FCM_SERVICE_ACCOUNT_JSON='):
                    in_json = True
                    json_start = line.split('=', 1)[1].strip()
                    if json_start.startswith('{'):
                        json_lines.append(json_start)
                    continue
                if in_json and line.strip().endswith('}'):
                    json_lines.append(line.strip())
                    break
                if in_json:
                    json_lines.append(line.strip())
            
            if json_lines:
                json_str = '\n'.join(json_lines)
                # Validate JSON
                json.loads(json_str)
                self.fcm_service_account_json = json_str
                
        except Exception:
            # If manual parsing fails, fall back to env var
            pass


settings = Settings()