# Aurora Alert App

A real-time aurora notification system that sends push notifications when aurora viewing conditions are favorable based on location, weather, and geomagnetic activity.

## Features

- **Real-time Aurora Data**: Uses NOAA SWPC Ovation Prime grid for aurora probability forecasts
- **Weather Integration**: Checks cloud coverage using OpenWeather API
- **Smart Notifications**: Only sends alerts during nighttime with favorable conditions
- **Location-based**: Customizable search radius around user location
- **Configurable Thresholds**: Users can set their own aurora probability thresholds
- **Anti-spam**: Cooldown period prevents notification flooding

## Quick Start

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the API server**:
   ```bash
   poetry run uvicorn src.api.main:app --reload
   ```

4. **Run the scheduler** (in another terminal):
   ```bash
   poetry run python -m src.scheduler
   ```

## API Endpoints

- `POST /subscribe` - Subscribe to aurora notifications
- `PATCH /prefs?token=<fcm_token>` - Update notification preferences  
- `DELETE /unsubscribe` - Unsubscribe from notifications
- `GET /status` - Check API health and active user count

## Environment Variables

- `OPENWEATHER_KEY` - OpenWeather API key for cloud data
- `FCM_SERVICE_ACCOUNT_JSON` - Firebase service account JSON (complete JSON as string)
- `RADIUS_KM` - Default search radius (250km)
- `PROB_THRESHOLD` - Default aurora probability threshold (15%)
- `CLOUD_MAX` - Maximum cloud coverage (40%)
- `COOLDOWN_H` - Hours between notifications (3h)

## Development

Run tests:
```bash
poetry run pytest
```

Code formatting:
```bash
poetry run black .
poetry run ruff check .
```

Type checking:
```bash
poetry run mypy src/
```

## Architecture

- `src/ingest/` - Data fetching from NOAA and OpenWeather APIs
- `src/engine/` - Core aurora probability and notification logic
- `src/api/` - FastAPI REST endpoints and database layer
- `src/notify/` - Firebase Cloud Messaging service
- `src/scheduler.py` - Main scheduler coordinating all components

## Deployment

Build with Docker:
```bash
docker build -t aurora-alert .
```

Deploy to Fly.io or your preferred platform.