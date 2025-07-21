# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Aurora Alert App** that sends real-time mobile/web notifications when aurora probability crosses a configurable threshold within a user's radius, accounting for daylight and cloud cover. The MVP targets Canada but works globally.

## Architecture

The project follows a microservices-style architecture with these core modules:

- **Data Ingestion** (`src/ingest/`): Fetches aurora probability data from NOAA SWPC Ovation Prime grid, planetary Kp index, and weather/cloud data from OpenWeather
- **Core Engine** (`src/engine/`): Processes grid data, calculates probabilities within user radius, applies daylight/cloud filters, and determines notification triggers
- **Notification Service** (`src/notify/`): Handles Firebase Cloud Messaging for push notifications
- **API Layer** (`src/api/`): FastAPI REST endpoints for user subscription management
- **Utilities** (`src/utils/`): Shared helper functions

## Development Setup

This is a Python project using Poetry for dependency management. Based on the project specification:

```bash
# Initialize Poetry and install dependencies
poetry init
poetry add httpx pydantic pandas numpy geopy shapely astral fastapi uvicorn apscheduler firebase-admin python-dotenv

# Development dependencies
poetry add --group dev pytest black ruff mypy

# Activate virtual environment
poetry shell

# Run the application
uvicorn src.api.main:app --reload

# Run tests
pytest tests/

# Linting and formatting
ruff check .
black .
mypy src/
```

## Environment Variables

Required environment variables (store in `.env`):
- `OPENWEATHER_KEY`: OpenWeather API key for cloud cover data
- `FCM_SERVER_KEY`: Firebase Cloud Messaging server key for notifications

## Key Data Sources

- **Aurora Data**: `https://services.swpc.noaa.gov/json/ovation_aurora_latest.json` (5-min updates)
- **Geomagnetic Data**: `https://services.swpc.noaa.gov/json/kp_index_now.json` (3-hr updates)  
- **Weather Data**: OpenWeather OneCall 3.0 API for cloud cover

## Core Decision Logic

The notification engine uses these configurable parameters:
- `RADIUS_KM`: 250km (user search radius)
- `PROB_THRESHOLD`: 15% (aurora probability threshold)
- `CLOUD_MAX`: 40% (maximum cloud coverage)
- `COOLDOWN_H`: 3 hours (minimum time between notifications)

Notification triggers when: `(prob ≥ threshold) ∧ night ∧ clouds_ok ∧ (now - last_notified > cooldown)`

## API Endpoints

- `POST /subscribe`: Register user with location and FCM token
- `PATCH /prefs`: Update user preferences (radius, threshold)
- `DELETE /unsubscribe`: Remove user subscription
- `GET /status`: Health check endpoint

## Deployment

The application is designed for deployment to Fly.io using Docker with a multi-stage build. The scheduler runs every 5 minutes to check conditions and send notifications.