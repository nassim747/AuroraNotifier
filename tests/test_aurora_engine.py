import pytest
import pandas as pd
from datetime import datetime
from src.engine.aurora_engine import AuroraEngine
from src.engine.models import User


@pytest.fixture
def aurora_engine():
    return AuroraEngine()


@pytest.fixture
def sample_aurora_data():
    return pd.DataFrame([
        {'lat': 45.5, 'lon': -73.6, 'prob': 25, 'power': 10},
        {'lat': 45.6, 'lon': -73.5, 'prob': 30, 'power': 15},
        {'lat': 45.4, 'lon': -73.7, 'prob': 20, 'power': 8},
        {'lat': 46.0, 'lon': -74.0, 'prob': 15, 'power': 5},
    ])


@pytest.fixture
def sample_user():
    return User(
        id=1,
        lat=45.5,
        lon=-73.6,
        radius_km=100,
        threshold=20,
        fcm_token="test_token",
        active=True
    )


def test_find_nearby_aurora_cells(aurora_engine, sample_aurora_data, sample_user):
    nearby = aurora_engine.find_nearby_aurora_cells(
        sample_user.lat, sample_user.lon, sample_aurora_data, sample_user.radius_km
    )
    
    assert len(nearby) > 0
    assert 'distance_km' in nearby.columns
    assert all(nearby['distance_km'] <= sample_user.radius_km)


def test_calculate_aurora_probability(aurora_engine, sample_aurora_data, sample_user):
    nearby = aurora_engine.find_nearby_aurora_cells(
        sample_user.lat, sample_user.lon, sample_aurora_data, sample_user.radius_km
    )
    
    max_prob, mean_prob = aurora_engine.calculate_aurora_probability(nearby)
    
    assert max_prob >= mean_prob
    assert max_prob <= 100
    assert mean_prob >= 0


def test_should_notify_user_high_probability(aurora_engine, sample_user):
    # High probability, night, low clouds
    should_notify = aurora_engine.should_notify_user(
        sample_user, 
        max_prob=30,
        mean_prob=25,
        cloud_coverage=20,
        is_night=True,
        timestamp=datetime.utcnow()
    )
    
    assert should_notify is True


def test_should_notify_user_low_probability(aurora_engine, sample_user):
    # Low probability
    should_notify = aurora_engine.should_notify_user(
        sample_user,
        max_prob=10,  # Below threshold
        mean_prob=8,
        cloud_coverage=20,
        is_night=True,
        timestamp=datetime.utcnow()
    )
    
    assert should_notify is False


def test_should_notify_user_daytime(aurora_engine, sample_user):
    # Daytime - should not notify
    should_notify = aurora_engine.should_notify_user(
        sample_user,
        max_prob=30,
        mean_prob=25,
        cloud_coverage=20,
        is_night=False,  # Daytime
        timestamp=datetime.utcnow()
    )
    
    assert should_notify is False


def test_should_notify_user_cloudy(aurora_engine, sample_user):
    # Too cloudy
    should_notify = aurora_engine.should_notify_user(
        sample_user,
        max_prob=30,
        mean_prob=25,
        cloud_coverage=80,  # Too cloudy
        is_night=True,
        timestamp=datetime.utcnow()
    )
    
    assert should_notify is False