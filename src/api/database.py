import sqlite3
from datetime import datetime
from typing import List, Optional
import logging
from ..engine.models import User
from ..utils.config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url.replace('sqlite:///', '')
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    radius_km INTEGER DEFAULT 250,
                    threshold INTEGER DEFAULT 15,
                    fcm_token TEXT NOT NULL UNIQUE,
                    last_notified TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    max_prob REAL,
                    mean_prob REAL,
                    cloud_coverage REAL,
                    is_night BOOLEAN,
                    should_notify BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def add_user(self, lat: float, lon: float, radius_km: int, threshold: int, fcm_token: str) -> Optional[User]:
        """Add a new user subscription."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO users (lat, lon, radius_km, threshold, fcm_token)
                    VALUES (?, ?, ?, ?, ?)
                ''', (lat, lon, radius_km, threshold, fcm_token))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return User(
                    id=user_id,
                    lat=lat,
                    lon=lon,
                    radius_km=radius_km,
                    threshold=threshold,
                    fcm_token=fcm_token,
                    created_at=datetime.utcnow(),
                    active=True
                )
        except sqlite3.IntegrityError:
            logger.warning(f"User with FCM token already exists")
            return None
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    def get_user_by_token(self, fcm_token: str) -> Optional[User]:
        """Get user by FCM token."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM users WHERE fcm_token = ? AND active = 1
                ''', (fcm_token,))
                
                row = cursor.fetchone()
                if row:
                    return User(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Error getting user by token: {e}")
            return None
    
    def update_user_preferences(self, fcm_token: str, radius_km: Optional[int] = None, 
                               threshold: Optional[int] = None) -> bool:
        """Update user preferences."""
        try:
            updates = []
            params = []
            
            if radius_km is not None:
                updates.append("radius_km = ?")
                params.append(radius_km)
            
            if threshold is not None:
                updates.append("threshold = ?")
                params.append(threshold)
            
            if not updates:
                return True
            
            params.append(fcm_token)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f'''
                    UPDATE users SET {", ".join(updates)}
                    WHERE fcm_token = ? AND active = 1
                ''', params)
                
                conn.commit()
                return conn.total_changes > 0
                
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def deactivate_user(self, fcm_token: str) -> bool:
        """Deactivate a user subscription."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE users SET active = 0 WHERE fcm_token = ?
                ''', (fcm_token,))
                
                conn.commit()
                return conn.total_changes > 0
                
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM users WHERE active = 1
                ''')
                
                users = []
                for row in cursor.fetchall():
                    users.append(User(**dict(row)))
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def update_last_notified(self, user_id: int, timestamp: datetime) -> bool:
        """Update the last notified timestamp for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE users SET last_notified = ? WHERE id = ?
                ''', (timestamp, user_id))
                
                conn.commit()
                return conn.total_changes > 0
                
        except Exception as e:
            logger.error(f"Error updating last notified: {e}")
            return False