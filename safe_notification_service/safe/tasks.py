from celery import app
from celery.utils.log import get_task_logger
from django.conf import settings

from safe_notification_service.firebase.client import (FirebaseClient,
                                                       MockedClient)

logger = get_task_logger(__name__)
oid = 'SAFE_NOTIFICATION_SERVICE'


firebase_client = None
try:
    firebase_client = FirebaseClient(credentials=settings.FIREBASE_AUTH_CREDENTIALS)
except AttributeError:
    logger.warning('FIREBASE_AUTH_CREDENTIALS not found in settings')
except Exception as e:
    logger.warning(e, exc_info=True)
finally:
    if not firebase_client:
        logger.warning('Using mocked notification client')
        firebase_client = MockedClient()


@app.shared_task(bind=True,
                 default_retry_delay=settings.NOTIFICATION_RETRY_DELAY_SECONDS,
                 max_retries=settings.NOTIFICATION_MAX_RETRIES)
def send_notification(self, message: str, push_token: str) -> None:
    """
    The task sends a Firebase Push Notification
    """
    try:
        firebase_client.send_message(message, push_token)
    except Exception as exc:
        str_exc = str(exc)
        if 'Requested entity was not found' in str_exc:
            # Push token not valid
            logger.warning('Push token not valid. Message=%s push-token=%s exception=%s' %
                          (message, push_token, str_exc),
                          exc_info=True)
        else:
            logger.error('Message=%s push-token=%s exception=%s' % (message, push_token, str_exc), exc_info=True)
            self.retry(exc=exc)
