from typing import Dict

from django.conf import settings

from celery import app
from celery.utils.log import get_task_logger

from safe_notification_service.firebase.client import FirebaseProvider

from .models import NotificationType

logger = get_task_logger(__name__)
oid = 'SAFE_NOTIFICATION_SERVICE'
firebase_client = FirebaseProvider()


def check_ios_enabled(message: Dict[str, any]) -> bool:
    """
    Check if ios should be enabled for the notification. Database will be checked: if `notification type` is not found,
    iOs is enabled, otherwise `ios` value of `notification type` in DB is used.
    :param message: Dictionary to send via Firebase
    :return: `True` if ios should be enabled, `False` otherwise
    """
    message_type = message.get('type')
    if message_type:
        try:
            return NotificationType.objects.get(name=message_type).ios
        except NotificationType.DoesNotExist:
            pass
    return True


@app.shared_task(bind=True,
                 default_retry_delay=settings.NOTIFICATION_RETRY_DELAY_SECONDS,
                 max_retries=settings.NOTIFICATION_MAX_RETRIES)
def send_notification(self, message: Dict[str, any], push_token: str) -> None:
    """
    The task sends a Firebase Push Notification
    """
    try:
        firebase_client.send_message(message, push_token, ios=self.check_ios_enabled(message))
    except Exception as exc:
        str_exc = str(exc)
        if 'Requested entity was not found' in str_exc:
            # Push token not valid
            logger.warning('Push token not valid. Message=%s push-token=%s exception=%s',
                           message, push_token, str_exc, exc_info=True)
        else:
            logger.error('Message=%s push-token=%s exception=%s', message, push_token, str_exc, exc_info=True)
            self.retry(exc=exc)
