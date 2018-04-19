from celery import app
from celery.utils.log import get_task_logger
from django.conf import settings

from gnosis_safe_push_service.firebase.client import FirebaseClient

logger = get_task_logger(__name__)
oid = 'SAFE_PUSH_SERVICE'


@app.shared_task(bind=True,
                 default_retry_delay=settings.NOTIFICATION_RETRY_DELAY_SECONDS,
                 max_retries=settings.NOTIFICATION_MAX_RETRIES)
def send_notification(self, message: str, push_token: str) -> None:
    """
    The task sends a Firebase Push Notification
    """
    try:
        firebase_client = FirebaseClient(credentials=settings.FIREBASE_AUTH_CREDENTIALS)
        firebase_client.send_message(message, push_token)
    except Exception as exc:
        logger.error(exc, exc_info=True)
        logger.info('Retry sending message with push_token=%s' % push_token)
        self.retry(exc=exc)
