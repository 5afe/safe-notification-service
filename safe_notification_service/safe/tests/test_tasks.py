from rest_framework.test import APITestCase

from ..tasks import check_ios_enabled
from .factories import NotificationTypeFactory


class TestTasks(APITestCase):

    def test_ios_enabled(self):
        message_type = 'safeCreation'
        message = {
            "type": message_type,
            "address": "0x4D953115678b15CE0B0396bCF95Db68003f86FB5",
        }
        self.assertTrue(check_ios_enabled(message))

        notification_type = NotificationTypeFactory(name=message_type, ios=False)
        self.assertFalse(check_ios_enabled(message))

        notification_type.ios = True
        notification_type.save()
        self.assertTrue(check_ios_enabled(message))

        notification_type.ios = False
        notification_type.save()
        notification_type.delete()
        self.assertTrue(check_ios_enabled(message))
