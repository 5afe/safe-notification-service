from django.urls import reverse

from eth_account import Account
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

        response = self.client.post(reverse('v1:auth-creation'), data=auth_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.get(owner=eth_account).push_token, auth_data['push_token'])
        response_json = response.json()
        self.assertEqual(response_json['owner'], eth_account)
        self.assertEqual(response_json['pushToken'], auth_data['push_token'])

        # Try repeating the request with same push token and different address
        eth_account, eth_key = get_eth_address_with_key()
        auth_data = get_auth_mock_data(key=eth_key, token=auth_data['push_token'])
        response = self.client.post(reverse('v1:auth-creation'), data=auth_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try repeating the request with different push token but same address
        auth_data = get_auth_mock_data(key=eth_key)
        response = self.client.post(reverse('v1:auth-creation'), data=auth_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.get(owner=eth_account).push_token, auth_data['push_token'])
        response_json = response.json()
        self.assertEqual(response_json['owner'], eth_account)
        self.assertEqual(response_json['pushToken'], auth_data['push_token'])

    def test_auth_fail(self):
        response = self.client.post(reverse('v1:auth-creation'), data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pairing_creation(self):
        another_device_address, another_device_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        data = get_pairing_mock_data(another_device_address=another_device_address,
                                     another_device_key=another_device_key, device_key=device_key)

        DeviceFactory(owner=another_device_address)
        DeviceFactory(owner=device_address)

        # Repeat same request (make sure creation is idempotent)
        for _ in range(0, 2):
            response = self.client.post(reverse('v1:pairing'), data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_json = response.json()
            self.assertEqual(set(response_json['devicePair']), {another_device_address, device_address})
            self.assertEqual(DevicePair.objects.count(), 2)

    def test_pairing_creation_without_auth(self):
        """
        Test pairing with devices that haven't been authenticated before
        """

        another_device_address, another_device_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        data = get_pairing_mock_data(another_device_address=another_device_address,
                                     another_device_key=another_device_key, device_key=device_key)

        response = self.client.post(reverse('v1:pairing'), data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(DevicePair.objects.count(), 2)

        self.assertIsNone(Device.objects.get(owner=another_device_address).push_token)
        self.assertIsNone(Device.objects.get(owner=device_address).push_token)

    def test_pairing_deletion(self):
        another_device = Account.create()
        device = Account.create()
        device_2 = Account.create()

        pairing_data = get_pairing_mock_data(another_device_address=another_device.address,
                                             another_device_key=another_device.privateKey, device_key=device.privateKey)

        pairing_data_2 = get_pairing_mock_data(another_device_address=device_2.address,
                                               another_device_key=device_2.privateKey, device_key=device.privateKey)

        DeviceFactory(owner=device.address)
        DeviceFactory(owner=another_device.address)
        DeviceFactory(owner=device_2.address)

        for pairing in (pairing_data, pairing_data_2):
            response = self.client.post(reverse('v1:pairing'), data=pairing, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        deletion_data = {
            'device': another_device.address,
            'signature': get_signature_json(another_device.address, device.privateKey)
        }

        response = self.client.delete(reverse('v1:pairing'), data=deletion_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(DevicePair.objects.filter(authorizing_device__owner=device.address).count(), 1)
        self.assertEqual(DevicePair.objects.filter(authorized_device__owner=device.address).count(), 1)

    def test_notification_creation(self):
        data = get_notification_mock_data()

        request = self.client.post(reverse('v1:notifications'), data=data, format='json')
        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)

        another_device_address, _ = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        d1 = DeviceFactory(owner=another_device_address)
        d2 = DeviceFactory(owner=device_address)
        DevicePairFactory(authorizing_device=d1, authorized_device=d2)
        DevicePairFactory(authorizing_device=d2, authorized_device=d1)

        data = get_notification_mock_data(devices=[another_device_address],
                                          eth_address_and_key=(device_address, device_key))

        request = self.client.post(reverse('v1:notifications'), data=data, format='json')

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

        with self.settings(NOTIFICATION_SERVICE_PASS='test'):
            response = self.client.post(reverse('v1:simple-notifications'), data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

            data['password'] = 'test'
            response = self.client.post(reverse('v1:simple-notifications'), data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
