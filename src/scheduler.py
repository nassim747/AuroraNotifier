import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

try:
    # Try relative imports (when run as module)
    from .ingest.aurora_data import AuroraDataFetcher
    from .ingest.weather_data import WeatherDataFetcher
    from .engine.aurora_engine import AuroraEngine
    from .notify.fcm_service import FCMService
    from .api.database import Database
    from .utils.config import settings
except ImportError:
    # Fall back to absolute imports (when run directly)
    from ingest.aurora_data import AuroraDataFetcher
    from ingest.weather_data import WeatherDataFetcher
    from engine.aurora_engine import AuroraEngine
    from notify.fcm_service import FCMService
    from api.database import Database
    from utils.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


class AuroraScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.aurora_fetcher = AuroraDataFetcher()
        self.weather_fetcher = WeatherDataFetcher()
        self.engine = AuroraEngine()
        self.fcm_service = FCMService()
        self.database = Database()
        
        self.setup_jobs()
    
    def setup_jobs(self):
        """Set up scheduled jobs."""
        # Main aurora check job every 5 minutes
        self.scheduler.add_job(
            self.check_aurora_conditions,
            trigger=IntervalTrigger(minutes=settings.check_interval_min),
            id='aurora_check',
            name='Check Aurora Conditions',
            max_instances=1,
            coalesce=True
        )
        
        # Health check job every hour
        self.scheduler.add_job(
            self.health_check,
            trigger=IntervalTrigger(hours=1),
            id='health_check',
            name='Health Check',
            max_instances=1
        )
    
    async def check_aurora_conditions(self):
        """Main job that checks aurora conditions and sends notifications."""
        try:
            logger.info("Starting aurora condition check...")
            
            # Get all active users
            users = self.database.get_active_users()
            if not users:
                logger.info("No active users, skipping check")
                return
            
            logger.info(f"Checking conditions for {len(users)} active users")
            
            # Fetch aurora data
            logger.info("Fetching aurora data...")
            aurora_data = await self.aurora_fetcher.fetch_all_data()
            aurora_df = aurora_data.get('ovation')
            
            if aurora_df is None or aurora_df.empty:
                logger.warning("No aurora data available, skipping check")
                return
            
            # Get unique user locations for weather data
            unique_locations = list(set((user.lat, user.lon) for user in users))
            logger.info(f"Fetching weather data for {len(unique_locations)} unique locations...")
            
            # Fetch weather data for all unique locations
            weather_data = await self.weather_fetcher.fetch_weather_for_multiple_locations(unique_locations)
            
            # Process alerts for all users
            logger.info("Processing aurora alerts...")
            alerts = self.engine.process_all_users(users, aurora_df, weather_data, datetime.utcnow())
            
            # Filter users who should be notified
            notifications_to_send = []
            for alert, user in zip(alerts, users):
                if alert.should_notify:
                    notifications_to_send.append((alert, user))
            
            logger.info(f"Found {len(notifications_to_send)} users to notify")
            
            # Send notifications
            if notifications_to_send:
                logger.info("Sending notifications...")
                results = await self.fcm_service.send_notifications_batch(notifications_to_send)
                
                # Update last_notified timestamp for successfully notified users
                current_time = datetime.utcnow()
                for (alert, user), i in zip(notifications_to_send, range(len(notifications_to_send))):
                    # Assuming notifications were sent in the same order
                    if i < results.get("sent", 0):
                        self.database.update_last_notified(user.id, current_time)
                
                logger.info(f"Notification results: {results}")
            else:
                logger.info("No notifications to send")
            
            logger.info("Aurora condition check completed successfully")
            
        except Exception as e:
            logger.error(f"Error in aurora condition check: {e}")
    
    async def health_check(self):
        """Periodic health check."""
        try:
            logger.info("Performing health check...")
            
            # Check database connection
            users = self.database.get_active_users()
            logger.info(f"Database OK - {len(users)} active users")
            
            # Test aurora data fetch
            aurora_data = await self.aurora_fetcher.fetch_ovation_data()
            if aurora_data is not None:
                logger.info(f"Aurora data OK - {len(aurora_data)} grid points")
            else:
                logger.warning("Aurora data fetch failed")
            
            # Test weather API (with a default location)
            weather_data = await self.weather_fetcher.fetch_weather_data(45.5, -73.6)  # Montreal
            if weather_data:
                logger.info("Weather data OK")
            else:
                logger.warning("Weather data fetch failed")
            
            logger.info("Health check completed")
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
    
    def start(self):
        """Start the scheduler."""
        logger.info("Starting Aurora Alert scheduler...")
        self.scheduler.start()
        logger.info(f"Scheduler started. Jobs: {[job.id for job in self.scheduler.get_jobs()]}")
    
    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping Aurora Alert scheduler...")
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    async def run_once(self):
        """Run the aurora check once for testing."""
        await self.check_aurora_conditions()


async def main():
    """Main function to run the scheduler."""
    scheduler = AuroraScheduler()
    
    try:
        scheduler.start()
        
        # Keep the scheduler running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())