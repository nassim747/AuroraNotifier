import asyncio
from typing import List, Dict, Any
import logging
from firebase_admin import credentials, messaging
import firebase_admin
from ..utils.config import settings
from ..engine.models import User, AuroraAlert

logger = logging.getLogger(__name__)


class FCMService:
    def __init__(self):
        self.app = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                import json
                
                # Parse the service account JSON from environment variable
                service_account_info = json.loads(settings.fcm_service_account_json)
                cred = credentials.Certificate(service_account_info)
                
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                self.app = firebase_admin.get_app()
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.app = None
    
    def create_aurora_notification(self, alert: AuroraAlert, user: User) -> messaging.Message:
        """Create a push notification message for aurora alert."""
        
        # Create notification title and body
        title = f"Aurora Alert! {alert.max_prob:.0f}% probability"
        
        # Create helpful message body
        body_parts = [
            f"Aurora probability: {alert.max_prob:.0f}% (avg: {alert.mean_prob:.0f}%)",
            f"Cloud coverage: {alert.cloud_coverage:.0f}%",
        ]
        
        if alert.is_night:
            body_parts.append("Look north for best viewing!")
        
        body = " • ".join(body_parts)
        
        # Create the message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                'max_prob': str(alert.max_prob),
                'mean_prob': str(alert.mean_prob),
                'cloud_coverage': str(alert.cloud_coverage),
                'is_night': str(alert.is_night),
                'timestamp': alert.timestamp.isoformat(),
                'user_lat': str(user.lat),
                'user_lon': str(user.lon),
            },
            token=user.fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='aurora_icon',
                    color='#4CAF50',
                    sound='aurora_alert',
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body,
                        ),
                        badge=1,
                        sound='aurora_alert.caf',
                    )
                )
            )
        )
        
        return message
    
    async def send_notification(self, alert: AuroraAlert, user: User) -> bool:
        """Send a notification to a single user."""
        if not self.app:
            logger.error("Firebase not initialized, cannot send notification")
            return False
        
        try:
            message = self.create_aurora_notification(alert, user)
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent notification to user {user.id}: {response}")
            return True
            
        except messaging.UnregisteredError:
            logger.warning(f"FCM token for user {user.id} is invalid or unregistered")
            return False
        except messaging.SenderIdMismatchError:
            logger.error(f"FCM sender ID mismatch for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Failed to send notification to user {user.id}: {e}")
            return False
    
    async def send_notifications_batch(self, alerts_and_users: List[tuple]) -> Dict[str, int]:
        """Send notifications to multiple users."""
        if not self.app:
            logger.error("Firebase not initialized, cannot send notifications")
            return {"sent": 0, "failed": 0}
        
        results = {"sent": 0, "failed": 0}
        
        # Create all messages
        messages = []
        users = []
        
        for alert, user in alerts_and_users:
            try:
                message = self.create_aurora_notification(alert, user)
                messages.append(message)
                users.append(user)
            except Exception as e:
                logger.error(f"Failed to create message for user {user.id}: {e}")
                results["failed"] += 1
        
        if not messages:
            return results
        
        try:
            # Send batch messages (up to 500 at a time)
            batch_response = messaging.send_all(messages)
            
            # Process results
            for i, response in enumerate(batch_response.responses):
                user = users[i]
                if response.success:
                    logger.info(f"Successfully sent notification to user {user.id}")
                    results["sent"] += 1
                else:
                    logger.error(f"Failed to send notification to user {user.id}: {response.exception}")
                    results["failed"] += 1
            
            logger.info(f"Batch notification results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to send batch notifications: {e}")
            results["failed"] += len(messages)
            return results
    
    async def send_test_notification(self, fcm_token: str) -> bool:
        """Send a test notification to verify FCM token."""
        if not self.app:
            logger.error("Firebase not initialized, cannot send test notification")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Aurora Alert Test",
                    body="Your aurora notifications are working! You'll receive alerts when conditions are favorable.",
                ),
                token=fcm_token,
            )
            
            response = messaging.send(message)
            logger.info(f"Test notification sent successfully: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return False