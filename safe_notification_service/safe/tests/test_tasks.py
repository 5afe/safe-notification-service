from rest_framework.test import APITestCase

from safe_notification_service.safe.models import DeviceTypeEnum

from ..tasks import send_notification_task, send_notification_to_devices
from .factories import (DeviceFactory, DevicePairFactory,
                        NotificationTypeFactory)


class TestTasks(APITestCase):
    def test_send_notification_to_devices(self):
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

        self.assertCountEqual(send_notification_to_devices(message, device_owners,
                                                           signer_device.owner),
                              [])

        # Devices must be paired to the signer device
        for device in devices:
            DevicePairFactory(
                authorizing_device=device,
                authorized_device=signer_device
            )

        self.assertCountEqual(send_notification_to_devices(message, device_owners,
                                                           signer_device.owner),
                              devices)

        notification_type = NotificationTypeFactory(
            name=message['type'],
            ios=None,
            android=0,
            extension=None
        )

        self.assertCountEqual(send_notification_to_devices(message, device_owners,
                                                           signer_device.owner),
                              [device_android])

        notification_type.ios = 0
        notification_type.save()
        self.assertCountEqual(send_notification_to_devices(message, device_owners,
                                                           signer_device.owner),
                              [device_android, device_ios])

        notification_type.extension = 0
        notification_type.save()
        self.assertCountEqual(send_notification_to_devices(message, device_owners,
                                                           signer_device.owner),
                              devices)

        notification_type.android = None
        notification_type.extension = None
        notification_type.ios = None
        notification_type.save()
        self.assertCountEqual(send_notification_to_devices(message, device_owners,
                                                           signer_device.owner),
                              [])

    def test_send_notification_task(self):
        message_type = 'safeCreation'
        message = {
            "type": message_type,
            "address": "0x4D953115678b15CE0B0396bCF95Db68003f86FB5",
        }
        push_token = 'test-123'

        self.assertEqual(send_notification_task.delay(message, push_token).get(),
                         'MockedResponse')
