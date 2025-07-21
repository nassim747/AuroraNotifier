import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import numpy as np
from geopy.distance import geodesic
from astral import LocationInfo
from astral.sun import sun
import logging

from .models import User, AuroraAlert
from ..utils.config import settings

logger = logging.getLogger(__name__)


class AuroraEngine:
    def __init__(self):
        self.radius_km = settings.radius_km
        self.prob_threshold = settings.prob_threshold
        self.cloud_max = settings.cloud_max
        self.cooldown_h = settings.cooldown_h
    
    def find_nearby_aurora_cells(self, user_lat: float, user_lon: float, 
                                aurora_df: pd.DataFrame, radius_km: int) -> pd.DataFrame:
        """Find aurora grid cells within radius of user location."""
        if aurora_df is None or aurora_df.empty:
            return pd.DataFrame()
        
        user_location = (user_lat, user_lon)
        nearby_cells = []
        
        for _, row in aurora_df.iterrows():
            cell_location = (row['lat'], row['lon'])
            distance = geodesic(user_location, cell_location).kilometers
            
            if distance <= radius_km:
                nearby_cells.append({
                    'lat': row['lat'],
                    'lon': row['lon'],
                    'prob': row['prob'],
                    'power': row.get('power', 0),
                    'distance_km': distance
                })
        
        return pd.DataFrame(nearby_cells)
    
    def calculate_aurora_probability(self, nearby_cells: pd.DataFrame) -> Tuple[float, float]:
        """Calculate max and mean aurora probability from nearby cells."""
        if nearby_cells.empty:
            return 0.0, 0.0
        
        max_prob = nearby_cells['prob'].max()
        mean_prob = nearby_cells['prob'].mean()
        
        return float(max_prob), float(mean_prob)
    
    def is_nighttime(self, lat: float, lon: float, timestamp: datetime) -> bool:
        """Check if it's nighttime (sun altitude < -6°) for aurora visibility."""
        try:
            location = LocationInfo(latitude=lat, longitude=lon)
            s = sun(location.observer, date=timestamp.date())
            
            # Check if current time is between sunset and sunrise
            if s['sunset'] <= timestamp.time() or timestamp.time() <= s['sunrise']:
                return True
            
            # Also check sun altitude for twilight
            from astral.sun import elevation
            sun_elevation = elevation(location.observer, timestamp)
            
            # Civil twilight threshold (-6°) for aurora visibility
            return sun_elevation < -6
            
        except Exception as e:
            logger.warning(f"Error calculating sun position for {lat},{lon}: {e}")
            # Default to nighttime if we can't calculate
            hour = timestamp.hour
            return hour < 6 or hour > 18
    
    def should_notify_user(self, user: User, max_prob: float, mean_prob: float, 
                          cloud_coverage: float, is_night: bool, timestamp: datetime) -> bool:
        """Determine if user should be notified based on all criteria."""
        
        # Check probability threshold
        if max_prob < user.threshold:
            logger.debug(f"User {user.id}: Probability {max_prob}% below threshold {user.threshold}%")
            return False
        
        # Check if it's nighttime
        if not is_night:
            logger.debug(f"User {user.id}: Daytime, no notification")
            return False
        
        # Check cloud coverage
        if cloud_coverage > self.cloud_max:
            logger.debug(f"User {user.id}: Too cloudy ({cloud_coverage}% > {self.cloud_max}%)")
            return False
        
        # Check cooldown period
        if user.last_notified:
            time_since_last = timestamp - user.last_notified
            if time_since_last < timedelta(hours=self.cooldown_h):
                logger.debug(f"User {user.id}: Still in cooldown period")
                return False
        
        logger.info(f"User {user.id}: All criteria met for notification")
        return True
    
    def process_user_alert(self, user: User, aurora_df: pd.DataFrame, 
                          cloud_coverage: float, timestamp: datetime) -> AuroraAlert:
        """Process aurora alert logic for a single user."""
        
        # Find nearby aurora cells
        nearby_cells = self.find_nearby_aurora_cells(
            user.lat, user.lon, aurora_df, user.radius_km
        )
        
        # Calculate probabilities
        max_prob, mean_prob = self.calculate_aurora_probability(nearby_cells)
        
        # Check if it's nighttime
        is_night = self.is_nighttime(user.lat, user.lon, timestamp)
        
        # Determine if user should be notified
        should_notify = self.should_notify_user(
            user, max_prob, mean_prob, cloud_coverage, is_night, timestamp
        )
        
        return AuroraAlert(
            user_id=user.id,
            max_prob=max_prob,
            mean_prob=mean_prob,
            cloud_coverage=cloud_coverage,
            is_night=is_night,
            should_notify=should_notify,
            timestamp=timestamp
        )
    
    def process_all_users(self, users: List[User], aurora_df: pd.DataFrame, 
                         weather_data: dict, timestamp: datetime) -> List[AuroraAlert]:
        """Process aurora alerts for all users."""
        alerts = []
        
        for user in users:
            # Find weather data for this user's location
            user_weather = None
            for weather in weather_data.get('weather_data', []):
                if (abs(weather['lat'] - user.lat) < 0.1 and 
                    abs(weather['lon'] - user.lon) < 0.1):
                    user_weather = weather
                    break
            
            cloud_coverage = user_weather['current_clouds'] if user_weather else 100
            
            alert = self.process_user_alert(user, aurora_df, cloud_coverage, timestamp)
            alerts.append(alert)
        
        return alerts