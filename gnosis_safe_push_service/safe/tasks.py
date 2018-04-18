from celery import app
from celery.utils.log import get_task_logger
from gnosis_safe_push_service.firebase.client import FirebaseClient
from django.conf import settings


logger = get_task_logger(__name__)
oid = 'SAFE_PUSH_SERVICE'


@app.shared_task(bind=True,
          default_retry_delay = settings.FIREBASE_NOTIFICATION_RETRY_DELAY,
          max_retries=settings.FIREBASE_MAX_NOTIFICATION_RETRIES)
def send_notification(self, message, push_token):
    """
    The task sends a Firebase Push Notification
    """
    try:
        client = FirebaseClient(credentials=settings.FIREBASE_AUTH_CREDENTIALS)
        client.send_message(message, push_token)
    except Exception as exc:
        logger.error(exc, exc_info=True)
        logger.info('Retry sending message with push_token: %s' % push_token)
        self.retry(exc=exc)
