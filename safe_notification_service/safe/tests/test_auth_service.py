from django.test import TestCase

from eth_account import Account

from ..models import Device, DeviceTypeEnum
from ..services import AuthServiceProvider


class TestAuthService(TestCase):
    def test_create_auth(self):
        auth_service = AuthServiceProvider()
        push_token = 'eZpZnaXNo0Y:APA91bE8QebofNECOmZUIsyYl0M85EDG9XdIqcew2G-3aUOPEobXbrIHPOdx-o8hKUIiqzcedL4f36y' \
                     'C8ZOjYnNTzhmugc2FHuTuMhQFQ9gc0IBwb4C35YvmWaY2uJjOLZa9i46cC4aS'
        push_token_2 = 'aBpZnaXNo0Y:APA91bE8QebofNECOmZUIsyYl0M85EDG9XdIqcew2G-3aUOPEobXbrIHPOdx-o8hKUIiqzcedL4f36y' \
                       'acZOjYnNTzhmugc2FHuTuMhQFQ9gc0IBwb4C35YvmWaY2uJjOLZa9i46cC4aS'
        build_number = 2
        version_name = '1.0.2'
        client = DeviceTypeEnum.ANDROID.name
        bundle = 'pm.gnosis.heimdall'

        owners = [Account.create().address for _ in range(3)]
        owners_2 = [Account.create().address for _ in range(2)]

        devices = auth_service.create_auth(push_token, build_number, version_name, client, bundle, owners)
        self.assertEqual(len(devices), len(owners))
        self.assertEqual(Device.objects.all().count(), len(owners))

        # We use the same push token but different owners, old owners get deleted
        devices = auth_service.create_auth(push_token, build_number, version_name, client, bundle, owners_2)
        self.assertEqual(len(devices), len(owners_2))
        self.assertEqual(Device.objects.all().count(), len(owners_2))
        self.assertEqual(Device.objects.filter(push_token=push_token).count(), len(owners_2))

        # We use same owners but different push token, push token gets updated
        devices = auth_service.create_auth(push_token_2, build_number, version_name, client, bundle, owners_2)
        self.assertEqual(len(devices), len(owners_2))
        self.assertEqual(Device.objects.all().count(), len(owners_2))
        self.assertEqual(Device.objects.filter(push_token=push_token_2).count(), len(owners_2))

        # We insert new owners with a new push token, they get inserted
        devices = auth_service.create_auth(push_token, build_number, version_name, client, bundle, owners)
        self.assertEqual(len(devices), len(owners))
        self.assertEqual(Device.objects.all().count(), len(owners) + len(owners_2))
        self.assertEqual(Device.objects.filter(push_token=push_token).count(), len(owners))
        self.assertEqual(Device.objects.filter(push_token=push_token_2).count(), len(owners_2))

        # We insert one owner with the `push_token_2`, old `owners_2` get deleted
        devices = auth_service.create_auth(push_token_2, build_number, version_name, client, bundle,
                                           [Account.create().address])
        self.assertEqual(len(devices), 1)
        self.assertEqual(Device.objects.all().count(), len(owners) + 1)
        self.assertEqual(Device.objects.filter(push_token=push_token).count(), len(owners))
        self.assertEqual(Device.objects.filter(push_token=push_token_2).count(), 1)
