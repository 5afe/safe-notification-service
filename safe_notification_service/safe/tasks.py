from typing import Dict, List, Optional

from django.conf import settings

from celery import app
from celery.utils.log import get_task_logger

from .models import Device
from .services.notification_service import (InvalidPushToken,
                                            NotificationServiceProvider,
                                            UnknownMessagingException)

logger = get_task_logger(__name__)


def send_notification_to_devices(message: Dict[str, any], devices: List[str],
                                 signer_address: Optional[str] = None) -> List[Device]:
    devices = NotificationServiceProvider().get_enabled_devices(message, devices, signer_address)
    for device in devices:
        send_notification_task.delay(message, device.push_token)
    return devices


@app.shared_task(bind=True,
                 default_retry_delay=settings.NOTIFICATION_RETRY_DELAY_SECONDS,
                 max_retries=settings.NOTIFICATION_MAX_RETRIES)
def send_notification_task(self, message: Dict[str, any], push_token: str) -> str:
    """
    The task sends a Firebase Push Notification
    """
    try:
        return NotificationServiceProvider().send_notification(message, push_token)
    except InvalidPushToken:
        pass
    except UnknownMessagingException as exc:
        self.retry(exc=exc)
