import os
from datetime import datetime
from typing import List, Optional
import logging
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from ..engine.models import User
from ..utils.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class UserDB(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    radius_km = Column(Integer, default=250)
    threshold = Column(Integer, default=15)
    fcm_token = Column(String, nullable=False, unique=True)
    last_notified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

class AlertDB(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    max_prob = Column(Float)
    mean_prob = Column(Float)
    cloud_coverage = Column(Float)
    is_night = Column(Boolean)
    should_notify = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Database:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_user(self, lat: float, lon: float, radius_km: int, threshold: int, fcm_token: str) -> Optional[User]:
        """Add a new user subscription."""
        try:
            with self.SessionLocal() as session:
                # Check if user already exists
                existing = session.query(UserDB).filter(UserDB.fcm_token == fcm_token).first()
                if existing:
                    logger.warning(f"User with FCM token already exists")
                    return None
                
                db_user = UserDB(
                    lat=lat,
                    lon=lon,
                    radius_km=radius_km,
                    threshold=threshold,
                    fcm_token=fcm_token,
                    created_at=datetime.utcnow(),
                    active=True
                )
                
                session.add(db_user)
                session.commit()
                session.refresh(db_user)
                
                return User(
                    id=db_user.id,
                    lat=db_user.lat,
                    lon=db_user.lon,
                    radius_km=db_user.radius_km,
                    threshold=db_user.threshold,
                    fcm_token=db_user.fcm_token,
                    last_notified=db_user.last_notified,
                    created_at=db_user.created_at,
                    active=db_user.active
                )
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    def get_user_by_token(self, fcm_token: str) -> Optional[User]:
        """Get user by FCM token."""
        try:
            with self.SessionLocal() as session:
                db_user = session.query(UserDB).filter(
                    UserDB.fcm_token == fcm_token,
                    UserDB.active == True
                ).first()
                
                if db_user:
                    return User(
                        id=db_user.id,
                        lat=db_user.lat,
                        lon=db_user.lon,
                        radius_km=db_user.radius_km,
                        threshold=db_user.threshold,
                        fcm_token=db_user.fcm_token,
                        last_notified=db_user.last_notified,
                        created_at=db_user.created_at,
                        active=db_user.active
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting user by token: {e}")
            return None
    
    def update_user_preferences(self, fcm_token: str, radius_km: Optional[int] = None, 
                               threshold: Optional[int] = None) -> bool:
        """Update user preferences."""
        try:
            with self.SessionLocal() as session:
                db_user = session.query(UserDB).filter(
                    UserDB.fcm_token == fcm_token,
                    UserDB.active == True
                ).first()
                
                if not db_user:
                    return False
                
                updated = False
                if radius_km is not None:
                    db_user.radius_km = radius_km
                    updated = True
                
                if threshold is not None:
                    db_user.threshold = threshold
                    updated = True
                
                if updated:
                    session.commit()
                
                return updated
                
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def deactivate_user(self, fcm_token: str) -> bool:
        """Deactivate a user subscription."""
        try:
            with self.SessionLocal() as session:
                db_user = session.query(UserDB).filter(
                    UserDB.fcm_token == fcm_token
                ).first()
                
                if db_user:
                    db_user.active = False
                    session.commit()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        try:
            with self.SessionLocal() as session:
                db_users = session.query(UserDB).filter(UserDB.active == True).all()
                
                users = []
                for db_user in db_users:
                    users.append(User(
                        id=db_user.id,
                        lat=db_user.lat,
                        lon=db_user.lon,
                        radius_km=db_user.radius_km,
                        threshold=db_user.threshold,
                        fcm_token=db_user.fcm_token,
                        last_notified=db_user.last_notified,
                        created_at=db_user.created_at,
                        active=db_user.active
                    ))
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def update_last_notified(self, user_id: int, timestamp: datetime) -> bool:
        """Update the last notified timestamp for a user."""
        try:
            with self.SessionLocal() as session:
                db_user = session.query(UserDB).filter(UserDB.id == user_id).first()
                
                if db_user:
                    db_user.last_notified = timestamp
                    session.commit()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating last notified: {e}")
            return False