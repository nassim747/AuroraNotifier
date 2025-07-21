import asyncio
from typing import Optional, Dict, Any
import httpx
from datetime import datetime
import logging
from ..utils.config import settings

logger = logging.getLogger(__name__)


class WeatherDataFetcher:
    def __init__(self):
        self.api_key = settings.openweather_key
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall"
    
    async def fetch_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather data including cloud coverage for a specific location."""
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'exclude': 'minutely,daily,alerts'  # We only need current and hourly
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                current_clouds = data.get('current', {}).get('clouds', 100)
                
                # Get next few hours of cloud data for better prediction
                hourly_clouds = []
                if 'hourly' in data:
                    for hour in data['hourly'][:6]:  # Next 6 hours
                        hourly_clouds.append(hour.get('clouds', 100))
                
                result = {
                    'lat': lat,
                    'lon': lon,
                    'current_clouds': current_clouds,
                    'hourly_clouds': hourly_clouds,
                    'timestamp': datetime.utcnow()
                }
                
                logger.debug(f"Weather data for {lat:.2f},{lon:.2f}: {current_clouds}% clouds")
                return result
                
        except httpx.RequestError as e:
            logger.error(f"Error fetching weather data for {lat},{lon}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing weather data: {e}")
            return None
    
    async def fetch_weather_for_multiple_locations(self, locations: list) -> Dict[str, Any]:
        """Fetch weather data for multiple locations concurrently."""
        tasks = []
        for lat, lon in locations:
            task = self.fetch_weather_data(lat, lon)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Weather fetch error: {result}")
        
        return {
            'weather_data': valid_results,
            'timestamp': datetime.utcnow()
        }