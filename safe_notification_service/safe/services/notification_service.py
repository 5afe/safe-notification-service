from logging import getLogger
from typing import Dict, List, Optional

from django.db.models import Q

from firebase_admin.messaging import UnregisteredError

from safe_notification_service.firebase.client import (FirebaseProvider,
                                                       MessagingClient)

from ..models import Device, DevicePair, DeviceTypeEnum, NotificationType

logger = getLogger(__name__)


class NotificationServiceException(Exception):
    pass


class InvalidPushToken(NotificationServiceException):
    pass


class UnknownMessagingException(NotificationServiceException):
    pass


class NotificationServiceProvider:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = NotificationService(FirebaseProvider())
        return cls.instance

    @classmethod
    def del_singleton(cls):
        if hasattr(cls, "instance"):
            del cls.instance


class NotificationService:
    def __init__(self, messaging_client: MessagingClient):
        self.messaging_client = messaging_client

    def _filter_devices_by_message_type(self, message: Dict[str, any],
                                        devices: List[Device]) -> List[Device]:
        """
        Filter notifications based on `NotificationType` and `Device` client. If notification is not configured
        (no `NotificationType` found) notification will be enabled for every client. Otherwise, configuration per
        client is followed
        :param message:
        :param devices:
        :return: Filtered list of devices, empty list if no device passed the filtering
        """
        if not devices:
            return []

        message_type = message.get('type')
        if not message_type:
            return devices
        else:
            try:
                notification_type = NotificationType.objects.get(name=message_type)
                return [device for device in devices
                        if notification_type.matches_device(device)]
            except NotificationType.DoesNotExist:
                return devices

    def get_enabled_devices(self,
                            message: Dict[str, any],
                            devices: List[str],
                            signer_address: Optional[str] = None) -> List[Device]:
        """
        Get `devices` enabled for this kind of notification. It lets out `devices` without `push_token`
        :param message:
        :param devices:
        :param signer_address: If not set, `DevicePairs` are not checked for sending notifications
        :return: Devices filtered
        """
        if signer_address:
            pairings = DevicePair.objects.filter(
                (Q(authorizing_device__owner__in=devices) & Q(authorized_device__owner=signer_address))
            ).select_related('authorizing_device')
            db_devices = [pairing.authorizing_device for pairing in pairings if pairing.authorizing_device.push_token]
        else:
            db_devices = Device.objects.filter(owner__in=devices).exclude(push_token=None)
        logger.info('Found %d paired devices, sender: %s, devices: %s' % (len(db_devices), signer_address, devices))
        filtered_devices = self._filter_devices_by_message_type(message, db_devices)
        logger.info('Remaining %d paired devices after filtering, sender: %s, devices: %s' % (len(filtered_devices),
                                                                                              signer_address,
                                                                                              filtered_devices))
        return filtered_devices

    def send_notification(self, message: Dict[str, any], push_token: str) -> str:
        try:
            return self.messaging_client.send_message(message, push_token)
        except UnregisteredError as exc:
            # Push token not valid
            str_exc = str(exc)
            logger.warning('Push token not valid. Message=%s push-token=%s exception=%s',
                           message, push_token, str_exc, exc_info=True)
            raise InvalidPushToken(str_exc) from exc
        except Exception as exc:
            str_exc = str(exc)
            logger.error('Message=%s push-token=%s exception=%s', message, push_token, str_exc, exc_info=True)
            raise UnknownMessagingException(str_exc) from exc
