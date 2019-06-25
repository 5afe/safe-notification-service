from django.test import TestCase

from .factories import DeviceFactory, DevicePairFactory, NotificationTypeFactory
from ..models import Device, DeviceTypeEnum
from ..services import NotificationServiceProvider


class TestNotificationService(TestCase):
    def test_get_enabled_devices(self):
        notification_service = NotificationServiceProvider()
        message_type = 'safeCreation'
        message = {
            "type": message_type,
            "address": "0x4D953115678b15CE0B0396bCF95Db68003f86FB5",
        }

        device_android = DeviceFactory(client=DeviceTypeEnum.ANDROID.value)
        device_extension = DeviceFactory(client=DeviceTypeEnum.EXTENSION.value)
        device_ios = DeviceFactory(client=DeviceTypeEnum.IOS.value)
        devices = [device_android, device_extension, device_ios]
        device_owners = [device.owner for device in devices]
        signer_device = DeviceFactory()

        # Needs pairing
        self.assertCountEqual(notification_service.get_enabled_devices(message, device_owners,
                                                                       signer_address=signer_device.owner),
                              [])

        # Withouth `signer_address` pairing is not required, so devices will be retrieved
        self.assertCountEqual(notification_service.get_enabled_devices(message, device_owners),
                              devices)

        # Devices must be paired to the signer device
        for device in devices:
            DevicePairFactory(
                authorizing_device=device,
                authorized_device=signer_device
            )

        for signer_address in (None, signer_device.owner):
            self.assertCountEqual(notification_service.get_enabled_devices(message, device_owners,
                                                                                 signer_address=signer_address),
                                        devices)

        notification_type = NotificationTypeFactory(
            name=message['type'],
            ios=False,
            android=True,
            extension=False
        )
        for signer_address in (None, signer_device.owner):
            self.assertCountEqual(notification_service.get_enabled_devices(message, device_owners,
                                                                                 signer_address=signer_address),
                                        [device_android])

        notification_type.ios = True
        notification_type.save()
        for signer_address in (None, signer_device.owner):
            self.assertCountEqual(notification_service.get_enabled_devices(message, device_owners,
                                                                                 signer_address=signer_address),
                                        [device_android, device_ios])

        notification_type.extension = True
        notification_type.save()
        for signer_address in (None, signer_device.owner):
            self.assertCountEqual(notification_service.get_enabled_devices(message, device_owners,
                                                                                 signer_address=signer_address),
                                        devices)

        notification_type.android = False
        notification_type.extension = False
        notification_type.ios = False
        notification_type.save()
        for signer_address in (None, signer_device.owner):
            self.assertCountEqual(notification_service.get_enabled_devices(message, device_owners,
                                                                                 signer_address=signer_address),
                                        [])
