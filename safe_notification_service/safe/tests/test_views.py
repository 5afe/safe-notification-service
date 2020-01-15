import json

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
        another_device_account = Account.create()
        device_account = Account.create()
        data = get_pairing_mock_data(another_device_account=another_device_account,
                                     device_account=device_account)

        DeviceFactory(owner=another_device_account.address)
        DeviceFactory(owner=device_account.address)

        # Repeat same request (make sure creation is idempotent)
        for _ in range(0, 2):
            response = self.client.post(reverse('v1:pairing'), data=data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_json = response.json()
            self.assertEqual(set(response_json['devicePair']), {another_device_account.address, device_account.address})
            self.assertEqual(DevicePair.objects.count(), 2)

    def test_pairing_creation_without_auth(self):
        """
        Test pairing with devices that haven't been authenticated before
        """

        another_device_account = Account.create()
        device_account = Account.create()
        data = get_pairing_mock_data(another_device_account=another_device_account,
                                     device_account=device_account)

        response = self.client.post(reverse('v1:pairing'), data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(DevicePair.objects.count(), 2)

        self.assertIsNone(Device.objects.get(owner=another_device_account.address).push_token)
        self.assertIsNone(Device.objects.get(owner=device_account.address).push_token)

    def test_pairing_deletion(self):
        another_device_account = Account.create()
        device_account = Account.create()
        device_2_account = Account.create()

        pairing_data = get_pairing_mock_data(another_device_account=another_device_account,
                                             device_account=device_account)

        pairing_data_2 = get_pairing_mock_data(another_device_account=device_2_account,
                                               device_account=device_account)

        DeviceFactory(owner=device_account.address)
        DeviceFactory(owner=another_device_account.address)
        DeviceFactory(owner=device_2_account.address)

        for pairing in (pairing_data, pairing_data_2):
            response = self.client.post(reverse('v1:pairing'), data=pairing, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        deletion_data = {
            'device': another_device_account.address,
            'signature': get_signature_json(another_device_account.address, device_account.key)
        }

        response = self.client.delete(reverse('v1:pairing'), data=deletion_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(DevicePair.objects.filter(authorizing_device__owner=device_account.address).count(), 1)
        self.assertEqual(DevicePair.objects.filter(authorized_device__owner=device_account.address).count(), 1)

    def test_notification_creation(self):
        data = get_notification_mock_data()

        request = self.client.post(reverse('v1:notifications'), data=data, format='json')
        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)

        another_device_account = Account.create()
        account = Account.create()
        d1 = DeviceFactory(owner=another_device_account.address)
        d2 = DeviceFactory(owner=account.address)
        DevicePairFactory(authorizing_device=d1, authorized_device=d2)
        DevicePairFactory(authorizing_device=d2, authorized_device=d1)

        data = get_notification_mock_data(devices=[another_device_account.address], account=account)
        request = self.client.post(reverse('v1:notifications'), data=data, format='json')
        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)

        # Test 4Kb message limit
        data = get_notification_mock_data(message=json.dumps({'my_message': 'A' * 4096}),
                                          devices=[another_device_account.address],
                                          account=account)
        request = self.client.post(reverse('v1:notifications'), data=data, format='json')
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(request.json()['message'][0], 'Ensure this field has no more than 4096 characters.')

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
