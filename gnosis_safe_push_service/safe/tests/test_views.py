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
from ..serializers import isoformat_without_ms
from .factories import get_signature_json, get_auth_mock_data, get_pairing_mock_data

faker = Faker()


class TestViews(APITestCase):

    def test_auth_creation(self):
        eth_account, eth_key = get_eth_address_with_key()
        auth_data = get_auth_mock_data(key=eth_key)

        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Device.objects.get(owner=eth_account).push_token, auth_data['push_token'])

    def test_auth_fail(self):
        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps({}),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pairing_creation(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        pairing_data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)

        Device.objects.create(push_token=faker.name(), owner=chrome_address)
        Device.objects.create(push_token=faker.name(), owner=device_address)

        request = self.client.post(reverse('v1:pairing'),
                                   data=json.dumps(pairing_data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)

        self.assertEquals(DevicePair.objects.count(), 2)

    def test_pairing_deletion(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        pairing_data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)

        Device.objects.create(push_token=faker.name(), owner=chrome_address)
        Device.objects.create(push_token=faker.name(), owner=device_address)

        request = self.client.post(reverse('v1:pairing'),
                                   data=json.dumps(pairing_data),
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
