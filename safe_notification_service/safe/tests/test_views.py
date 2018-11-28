import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from safe_notification_service.ether.tests.factories import \
    get_eth_address_with_key

from ..models import Device, DevicePair
from .factories import (DeviceFactory, DevicePairFactory, get_auth_mock_data,
                        get_notification_mock_data, get_pairing_mock_data,
                        get_signature_json)

faker = Faker()


class TestViews(APITestCase):

    def test_auth_creation(self):
        eth_account, eth_key = get_eth_address_with_key()
        auth_data = get_auth_mock_data(key=eth_key)

        response = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.get(owner=eth_account).push_token, auth_data['push_token'])
        response_json = response.json()
        self.assertEqual(response_json['owner'], eth_account)
        self.assertEqual(response_json['pushToken'], auth_data['push_token'])

        # Try repeating the request with same push token and address
        response = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try repeating the request with different push token but same address
        auth_data = get_auth_mock_data(key=eth_key)
        response = self.client.post(reverse('v1:auth-creation'), data=json.dumps(auth_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.get(owner=eth_account).push_token, auth_data['push_token'])
        response_json = response.json()
        self.assertEqual(response_json['owner'], eth_account)
        self.assertEqual(response_json['pushToken'], auth_data['push_token'])

    def test_auth_fail(self):
        response = self.client.post(reverse('v1:auth-creation'), data=json.dumps({}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pairing_creation(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)

        DeviceFactory(owner=chrome_address)
        DeviceFactory(owner=device_address)

        # Repeat same request (make sure creation is idempotent)
        for _ in range(0, 2):
            response = self.client.post(reverse('v1:pairing'),
                                        data=json.dumps(data),
                                        content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_json = response.json()
            self.assertEqual(set(response_json['devicePair']), set([chrome_address, device_address]))
            self.assertEqual(DevicePair.objects.count(), 2)

    def test_pairing_creation_without_auth(self):
        """
        Test pairing with devices that haven't been authenticated before
        """

        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)

        response = self.client.post(reverse('v1:pairing'),
                                    data=json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(DevicePair.objects.count(), 2)

        self.assertIsNone(Device.objects.get(owner=chrome_address).push_token)
        self.assertIsNone(Device.objects.get(owner=device_address).push_token)

    def test_pairing_deletion(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        pairing_data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)

        DeviceFactory(owner=chrome_address)
        DeviceFactory(owner=device_address)

        response = self.client.post(reverse('v1:pairing'),
                                    data=json.dumps(pairing_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        deletion_data = {
            'device': device_address,
            'signature': get_signature_json(device_address, device_key)
        }

        response = self.client.delete(reverse('v1:pairing'),
                                      data=json.dumps(deletion_data),
                                      content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(DevicePair.DoesNotExist):
            DevicePair.objects.get(authorizing_device__owner=device_address)

        with self.assertRaises(DevicePair.DoesNotExist):
            DevicePair.objects.get(authorized_device__owner=device_address)

    def test_notification_creation(self):
        data = get_notification_mock_data()

        request = self.client.post(reverse('v1:notifications'),
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)

        chrome_address, _ = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        d1 = DeviceFactory(owner=chrome_address)
        d2 = DeviceFactory(owner=device_address)
        DevicePairFactory(authorizing_device=d1, authorized_device=d2)
        DevicePairFactory(authorizing_device=d2, authorized_device=d1)

        data = get_notification_mock_data(devices=[chrome_address], eth_address_and_key=(device_address, device_key))

        request = self.client.post(reverse('v1:notifications'),
                                   data=json.dumps(data),
                                   content_type='application/json')

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)

    def test_simple_notification_creation(self):
        random_address, _ = get_eth_address_with_key()
        message = '{}'
        data = {
            'devices': [random_address],
            'message': message,
        }
        response = self.client.post(reverse('v1:simple-notifications'), data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        device_pair = DevicePairFactory()
        d1 = device_pair.authorizing_device
        d2 = device_pair.authorized_device

        data = {
            'devices': [d1.owner, d2.owner],
            'message': message,
        }
        response = self.client.post(reverse('v1:simple-notifications'), data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
