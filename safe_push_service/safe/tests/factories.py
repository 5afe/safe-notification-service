import json
from datetime import timedelta

from django.utils import timezone
from faker import Factory as FakerFactory
from faker import Faker

from safe_push_service.ether.signing import EthereumSigner
from safe_push_service.ether.tests.factories import \
    get_eth_address_with_key

from ..serializers import isoformat_without_ms

fakerFactory = FakerFactory.create()
faker = Faker()


def get_signature_json(message, key):
    ethereum_signer = EthereumSigner(message, key)
    v, r, s = ethereum_signer.v, ethereum_signer.r, ethereum_signer.s

    return {
        'v': v,
        'r': r,
        's': s
    }


def get_bad_signature(message, key):
    ethereum_signer = EthereumSigner(message, key)
    v, r, s = ethereum_signer.v, ethereum_signer.r, ethereum_signer.s

    return {
        'v': v * 5,
        'r': r + 8,
        's': s - 2
    }


def get_auth_mock_data(key, token=None):
    """ Generates auth dictionary data """
    if not token:
        token = faker.name()

    signature = get_signature_json(token, key)

    return {
        'push_token': token,
        'signature': signature
    }


def get_pairing_mock_data(expiration_date=None, chrome_key=None, chrome_address=None, device_key=None):
    """ Generates a dictionary data for pairing purposes """
    if not expiration_date:
        expiration_date = isoformat_without_ms((timezone.now() + timedelta(days=2)))
    if not chrome_address or not chrome_key:
        chrome_address, chrome_key = get_eth_address_with_key()
    if not device_key:
        device_address, device_key = get_eth_address_with_key()

    return {
        "temporary_authorization": {
            "expiration_date": expiration_date,
            "signature": get_signature_json(expiration_date, chrome_key),
        },
        "signature":  get_signature_json(chrome_address, device_key)
    }


def get_notification_mock_data(devices=None):
    """ Generates a dictionary data specifying a notification message """
    message = json.dumps({'title': faker.name()})
    eth_address, eth_key = get_eth_address_with_key()
    eth_address2, _ = get_eth_address_with_key()
    eth_address3, _ = get_eth_address_with_key()

    if not devices:
        devices = [eth_address2, eth_address3]

    return {
        'devices': devices,
        'message': message,
        'signature': get_signature_json(message, eth_key),
    }
