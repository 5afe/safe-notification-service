from logging import getLogger
from typing import List

from safe_notification_service.firebase.client import (FirebaseProvider,
                                                       MessagingClient)

from ..models import Device, DeviceTypeEnum

logger = getLogger(__name__)


class AuthServiceException(Exception):
    pass


class InvalidPushToken(AuthServiceException):
    pass


class AuthServiceProvider:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = AuthService(FirebaseProvider())
        return cls.instance

    @classmethod
    def del_singleton(cls):
        if hasattr(cls, "instance"):
            del cls.instance


class AuthService:
    def __init__(self, messaging_client: MessagingClient):
        self.messaging_client = messaging_client

    def verify_push_token(self, push_token: str):
        """
        Checks if push token is valid
        :param push_token: Firebase push token
        :return: `True` if valid, `False` otherwise
        """
        return self.messaging_client.verify_token(push_token)

    def create_auth(self, push_token: str, build_number: int, version_name: str, client: str, bundle: str,
                    owners: List[str]) -> List[Device]:

        assert owners, 'At least one owner must be provided'

        if not self.verify_push_token(push_token):
            raise InvalidPushToken(push_token)

        devices = []
        client = client.upper()
        for owner in owners:
            device, _ = Device.objects.update_or_create(owner=owner, defaults={
                'push_token': push_token,
                'build_number': build_number,
                'version_name': version_name,
                'client': DeviceTypeEnum[client].value,
                'bundle': bundle,
            })
            devices.append(device)
            logger.info('Owner=%s registered device with client=%s, bundle=%s, version_name=%s,'
                        'build_number=%d and push_token=%s',
                        owner, client, bundle, version_name, build_number, push_token)

        # Delete existing owners linked to this push token
        Device.objects.exclude(owner__in=owners).filter(push_token=push_token).delete()
        return devices
