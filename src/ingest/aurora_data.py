import asyncio
from typing import List, Dict, Any, Optional
import httpx
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuroraDataFetcher:
    def __init__(self):
        self.ovation_url = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
        self.kp_url = "https://services.swpc.noaa.gov/json/kp_index_now.json"
    
    async def fetch_ovation_data(self) -> Optional[pd.DataFrame]:
        """Fetch latest Ovation Prime grid data from NOAA SWPC."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.ovation_url, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    logger.warning("No Ovation data received")
                    return None
                
                df = pd.DataFrame(data)
                df['timestamp'] = datetime.utcnow()
                
                # Rename columns to match our expected format
                df = df.rename(columns={
                    'GeomagneticLat': 'lat',
                    'GeomagneticLon': 'lon',
                    'Probability': 'prob',
                    'Power': 'power'
                })
                
                logger.info(f"Fetched {len(df)} aurora probability grid points")
                return df
                
        except httpx.RequestError as e:
            logger.error(f"Error fetching Ovation data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing Ovation data: {e}")
            return None
    
    async def fetch_kp_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch current Kp index data from NOAA SWPC."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.kp_url, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    logger.warning("No Kp data received")
                    return None
                
                logger.info(f"Fetched {len(data)} Kp index entries")
                return data
                
        except httpx.RequestError as e:
            logger.error(f"Error fetching Kp data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing Kp data: {e}")
            return None
    
    async def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch both Ovation and Kp data concurrently."""
        ovation_task = self.fetch_ovation_data()
        kp_task = self.fetch_kp_data()
        
        ovation_data, kp_data = await asyncio.gather(ovation_task, kp_task)
        
        return {
            'ovation': ovation_data,
            'kp': kp_data,
            'timestamp': datetime.utcnow()
        }