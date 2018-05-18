from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from faker import Faker
from rest_framework.exceptions import ValidationError

from safe_notification_service.ether.signing import EthereumSignedMessage
from safe_notification_service.ether.tests.factories import \
    get_eth_address_with_key

from ..serializers import (AuthSerializer, GoogleInAppPurchaseSerializer,
                           NotificationSerializer, PairingDeletionSerializer,
                           PairingSerializer, isoformat_without_ms)
from .factories import (get_auth_mock_data, get_bad_signature,
                        get_google_billing_test_data,
                        get_notification_mock_data, get_pairing_mock_data,
                        get_signature_json)

faker = Faker()


class TestSerializers(TestCase):

    def test_auth_serializer(self):
        eth_address, eth_key = get_eth_address_with_key()
        data = get_auth_mock_data(eth_key)

        ethereum_signed_message = EthereumSignedMessage(data['push_token'], data['signature']['v'], data['signature']['r'], data['signature']['s'])

        push_token_hash = ethereum_signed_message.message_hash

        auth_serializer = AuthSerializer(data=data)

        self.assertTrue(auth_serializer.is_valid())

        self.assertEqual(auth_serializer.validated_data['message_hash'], push_token_hash)

        self.assertEqual(auth_serializer.validated_data['signing_address'], eth_address)

        bad_auth_data = {
            'push_token': data['push_token'],
            'signature': get_bad_signature(data['push_token'], eth_key)
        }

        auth_serializer = AuthSerializer(data=bad_auth_data)

        self.assertRaises(ValidationError, auth_serializer.is_valid, raise_exception=True)

    def test_pairing_serializer(self):
        chrome_address, chrome_key = get_eth_address_with_key()
        device_address, device_key = get_eth_address_with_key()
        data = get_pairing_mock_data(chrome_address=chrome_address, chrome_key=chrome_key, device_key=device_key)
        pairing_serializer = PairingSerializer(data=data)

        self.assertTrue(pairing_serializer.is_valid())

        self.assertEqual(chrome_address,
                         pairing_serializer.validated_data['temporary_authorization']['signing_address'])

        self.assertEqual(device_address, pairing_serializer.validated_data['signing_address'])

    def test_pairing_with_date_exceeded(self):
        expiration_date = isoformat_without_ms(timezone.now() - timedelta(days=2))
        data = get_pairing_mock_data(expiration_date=expiration_date)

        pairing_serializer = PairingSerializer(data=data)
        self.assertFalse(pairing_serializer.is_valid())
        self.assertTrue('expiration_date' in pairing_serializer.errors['temporary_authorization'])

    def test_pairing_with_date_invalid_format(self):
        expiration_date = (timezone.now() + timedelta(days=2)).isoformat()
        data = get_pairing_mock_data(expiration_date=expiration_date)
        pairing_serializer = PairingSerializer(data=data)
        self.assertFalse(pairing_serializer.is_valid())
        self.assertTrue('expiration_date' in pairing_serializer.errors['temporary_authorization'])

    def test_pairing_with_same_address(self):
        eth_address, eth_key = get_eth_address_with_key()

        expiration_date = isoformat_without_ms((timezone.now() + timedelta(days=2)))

        data = {
            "temporary_authorization": {
                "expiration_date": expiration_date,
                "signature": get_signature_json(expiration_date, eth_key),
            },
            "signature":  get_signature_json(eth_address, eth_key)
        }

        pairing_serializer = PairingSerializer(data=data)
        self.assertFalse(pairing_serializer.is_valid())
        self.assertTrue('non_field_errors' in pairing_serializer.errors)

    def test_pairing_deletion_serializer(self):
        device_address, device_key = get_eth_address_with_key()

        deletion_data = {
            'device': device_address,
            'signature': get_signature_json(device_address, device_key)
        }
        remove_pairing = PairingDeletionSerializer(data=deletion_data)
        self.assertTrue(remove_pairing.is_valid())

    def test_notification_serializer(self):
        notification_data = get_notification_mock_data()
        serializer = NotificationSerializer(data=notification_data)
        self.assertTrue(serializer.is_valid())
        self.assertFalse(serializer.save())

        # Message no json compliant
        notification_data = get_notification_mock_data()
        notification_data['message'] = 'NoValid{Json}'
        serializer = NotificationSerializer(data=notification_data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue('message' in serializer.errors)

        # Bad format
        invalid_notification_data = get_notification_mock_data(devices=['0x0', '0x1'])
        serializer = NotificationSerializer(data=invalid_notification_data)
        self.assertFalse(serializer.is_valid())

        # Bad checksum
        invalid_notification_data = get_notification_mock_data(devices=['0xBBc1069ba4806e632fd11fAc9336b1f9dbf074a90EEA861d0b79cf256127abF3',
                                                                        '0xAAc1066ba4806e632fd11fBc9336b1f9dbf074a90ecc861d0b79cf256127ABF3'])
        serializer = NotificationSerializer(data=invalid_notification_data)
        self.assertFalse(serializer.is_valid())

        # Duplicated addresses
        address, _ = get_eth_address_with_key()
        invalid_notification_data = get_notification_mock_data(devices=[address, address])
        serializer = NotificationSerializer(data=invalid_notification_data)
        self.assertFalse(serializer.is_valid())

        # No addresses
        invalid_notification_data['devices'] = []
        serializer = NotificationSerializer(data=invalid_notification_data)
        self.assertFalse(serializer.is_valid())

    def test_notification_serializer_sending_itself(self):
        device_address, device_key = get_eth_address_with_key()
        message = faker.name()

        data = {
            'devices': [device_address],
            'message': message,
            'signature': get_signature_json(message, device_key)
        }

        notification_serializer = NotificationSerializer(data=data)
        self.assertFalse(notification_serializer.is_valid())

    def test_google_in_app_purchase_serializer(self):
        app_public_key, purchase_json, purchase_signature = get_google_billing_test_data()

        with self.settings(GOOGLE_BILLING_PUBLIC_KEY_BASE64=app_public_key):

            data = {
                'signed_data': purchase_json,
                'signature': purchase_signature,
            }

            google_in_app_purchase_serializer = GoogleInAppPurchaseSerializer(data=data)
            self.assertTrue(google_in_app_purchase_serializer.is_valid())
            self.assertTrue(isinstance(google_in_app_purchase_serializer.validated_data['signed_data'], dict))

            data = {
                'signed_data': purchase_json.replace('{', '}'),
                'signature': purchase_signature,
            }

            google_in_app_purchase_serializer = GoogleInAppPurchaseSerializer(data=data)
            self.assertFalse(google_in_app_purchase_serializer.is_valid())
            self.assertTrue('signed_data' in google_in_app_purchase_serializer.errors)
