import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from safe_notification_service.ether.tests.factories import \
    get_eth_address_with_key

from ..models import Device, DevicePair
from .factories import (get_auth_mock_data, get_notification_mock_data,
                        get_pairing_mock_data, get_signature_json)

faker = Faker()


class TestViews(APITestCase):

    def test_auth_creation(self):
        eth_account, eth_key = get_eth_address_with_key()
        auth_data = get_auth_mock_data(key=eth_key)

        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.get(owner=eth_account).push_token, auth_data['push_token'])
        response = request.json()
        self.assertEqual(response['owner'], eth_account)
        self.assertEqual(response['pushToken'], auth_data['push_token'])

        # Try repeating the request with same push token and address
        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_400_BAD_REQUEST)

        # Try repeating the request with different push token but same address
        auth_data = get_auth_mock_data(key=eth_key)
        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.get(owner=eth_account).push_token, auth_data['push_token'])
        response = request.json()
        self.assertEqual(response['owner'], eth_account)
        self.assertEqual(response['pushToken'], auth_data['push_token'])

    def test_auth_fail(self):
        request = self.client.post(reverse('v1:auth-creation'), data=json.dumps({}),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pairing_creation(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)

        Device.objects.create(push_token=faker.name(), owner=chrome_address)
        Device.objects.create(push_token=faker.name(), owner=device_address)

        # Repeat same request (make sure creation is idempotent)
        for _ in range(0, 2):
            request = self.client.post(reverse('v1:pairing'),
                                       data=json.dumps(data),
                                       content_type='application/json')
            self.assertEquals(request.status_code, status.HTTP_201_CREATED)
            response = request.json()
            self.assertEqual(set(response['devicePair']), set([chrome_address, device_address]))
            self.assertEquals(DevicePair.objects.count(), 2)

    def test_pairing_creation_without_auth(self):
        """
        Test pairing with devices that haven't been authenticated before
        """

        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)

        request = self.client.post(reverse('v1:pairing'),
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_201_CREATED)

        self.assertEquals(DevicePair.objects.count(), 2)

        self.assertIsNone(Device.objects.get(owner=chrome_address).push_token)
        self.assertIsNone(Device.objects.get(owner=device_address).push_token)

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

    def test_notification_creation(self):
        data = get_notification_mock_data()

        request = self.client.post(reverse('v1:notifications'),
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_404_NOT_FOUND)

        chrome_address, _ = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        d1 = Device.objects.create(push_token=faker.name(), owner=chrome_address)
        d2 = Device.objects.create(push_token=faker.name(), owner=device_address)
        DevicePair.objects.create(authorizing_device=d1, authorized_device=d2)
        DevicePair.objects.create(authorizing_device=d2, authorized_device=d1)

        data = get_notification_mock_data(devices=[chrome_address], eth_address_and_key=(device_address, device_key))

        request = self.client.post(reverse('v1:notifications'),
                                   data=json.dumps(data),
                                   content_type='application/json')

        self.assertEquals(request.status_code, status.HTTP_204_NO_CONTENT)
