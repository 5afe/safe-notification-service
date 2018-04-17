import json
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from gnosis_safe_push_service.ether.tests.factories import \
    get_eth_address_with_key

from ..models import Device, DevicePair
from .factories import get_signature_json
from ..serializers import isoformat_without_ms

faker = Faker()


class TestViews(APITestCase):

    def test_auth_creation(self):
        eth_account, eth_key = get_eth_address_with_key()
        push_token = faker.name()
        signature = get_signature_json(push_token, eth_key)
        auth_data = {
            'pushToken': push_token,
            'signature': signature
        }

        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Device.objects.get(owner=eth_account).push_token, push_token)

    def test_auth_fail(self):
        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps({}),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pairing_creation(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()

        expiration_date = isoformat_without_ms(timezone.now() + timedelta(days=2))

        data = {
            "temporary_authorization": {
                "expiration_date": expiration_date,
                "signature": get_signature_json(expiration_date, chrome_key),
            },
            "signature": get_signature_json(chrome_address, device_key)
        }

        Device.objects.create(push_token=faker.name(), owner=chrome_address)
        Device.objects.create(push_token=faker.name(), owner=device_address)

        request = self.client.post(reverse('v1:pairing'),
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)

        self.assertEquals(DevicePair.objects.count(), 2)

    def test_pairing_deletion(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()

        expiration_date = isoformat_without_ms(timezone.now() + timedelta(days=2))

        data = {
            "temporary_authorization": {
                "expiration_date": expiration_date,
                "signature": get_signature_json(expiration_date, chrome_key),
            },
            "signature": get_signature_json(chrome_address, device_key)
        }

        Device.objects.create(push_token=faker.name(), owner=chrome_address)
        Device.objects.create(push_token=faker.name(), owner=device_address)

        request = self.client.post(reverse('v1:pairing'),
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)

        deletion_data = {
            'device': device_address,
            'signature': get_signature_json(device_address, device_key)
        }

        request = self.client.delete(reverse('v1:pairing'),
                                     data=json.dumps(deletion_data),
                                     content_type='application/json')

        self.assertEquals(request.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(DevicePair.DoesNotExist):
            DevicePair.objects.get(authorizing_device__owner=device_address)

        with self.assertRaises(DevicePair.DoesNotExist):
            DevicePair.objects.get(authorized_device__owner=device_address)