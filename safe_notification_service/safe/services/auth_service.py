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

    def create_auth(self, push_token: str, build_number: int, version_name: str, client: int, bundle: str,
                    owners: List[str]) -> List[Device]:

        if not self.messaging_client.verify_token(push_token):
            raise InvalidPushToken(push_token)

        devices = []
        for owner in owners:
            device, _ = Device.objects.update_or_create(owner=owner, defaults={
                'push_token': push_token,
                'build_number': build_number,
                'version_name': version_name,
                'client': DeviceTypeEnum[client.upper()].value,
                'bundle': bundle,
            })
            devices.append(device)
        return devices
