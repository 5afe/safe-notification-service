from typing import Dict, List

from django.conf import settings
from django.urls import reverse

from eth_account import Account
from ethereum.utils import sha3
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from safe_notification_service.ether.tests.factories import \
    get_eth_address_with_key

from ..models import Device, DevicePair, DeviceTypeEnum
from .factories import (DeviceFactory, DevicePairFactory, get_auth_mock_data,
                        get_notification_mock_data, get_pairing_mock_data,
                        get_signature_json)

faker = Faker()


class TestViewsV2(APITestCase):

    def _sign_auth(self, data: Dict[str, any], accounts: List[Account]) -> List[Dict[any, str]]:
        prefix = settings.ETH_HASH_PREFIX
        data_hash = sha3(prefix + data['push_token'] + str(data['build_number']) + data['version_name'] +
                         data['client'] + data['bundle'])
        signatures = []
        for account in accounts:
            signature = account.signHash(data_hash)
            signatures.append({
                'r': signature['r'],
                's': signature['s'],
                'v': signature['v'],
            })
        return signatures

    def test_auth_creation_v2(self):
        url = reverse('v2:auth-creation')
        account = Account.create()
        owner = account.address
        push_token = 'GGGGGGGGGGGGGGGG-NNNNNNNNNN-OOOOOOOOO-SSSSSSSS-IIIIII-wait-for-it-SSSSSSSSSS'
        build_number = 1644
        version_name = '1.0.0-beta'
        client = 'android'
        bundle = 'pm.gnosis.heimdall'
        data = {
            'push_token': push_token,
            'build_number': build_number,
            'version_name': version_name,
            'client': client,
            'bundle': bundle,
        }

        data['signatures'] = self._sign_auth(data, [account])
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        self.assertEqual(response_json[0]['owner'], owner)
        self.assertEqual(response_json[0]['pushToken'], push_token)

        device = Device.objects.get(owner=owner)
        self.assertEqual(device.push_token, push_token)
        self.assertEqual(device.build_number, build_number)
        self.assertEqual(device.version_name, version_name)
        self.assertEqual(device.client, DeviceTypeEnum[client.upper()].value)
        self.assertEqual(device.bundle, bundle)
        self.assertEqual(Device.objects.count(), 1)

        push_token = 'GGGGGGGGGGGGGGGG-NNNNNNNNNN-OOOOOOOOO-SSSSSSSS-IIIIII-dont-wait-for-it-SSSSSSSSSS'
        data['push_token'] = 'GGGGGGGGGGGGGGGG-NNNNNNNNNN-OOOOOOOOO-SSSSSSSS-IIIIII-dont-wait-for-it-SSSSSSSSSS'
        accounts = [account, Account.create(), Account.create()]
        owners = [a.address for a in accounts]
        data['signatures'] = self._sign_auth(data, accounts)
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        self.assertEqual(len(response_json), 3)
        response_owners = set([result['owner'] for result in response_json])
        self.assertEqual(response_owners, set(owners))
        self.assertEqual(Device.objects.count(), 3)

        for result in response_json:
            self.assertEqual(result['pushToken'], push_token)
            self.assertEqual(result['buildNumber'], build_number)
            self.assertEqual(result['client'], client.lower())
            self.assertEqual(result['bundle'], bundle)
