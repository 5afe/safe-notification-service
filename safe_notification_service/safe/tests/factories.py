import json
from datetime import timedelta
from typing import Tuple

from django.utils import timezone

import factory
from faker import Faker

from safe_notification_service.ether.signing import EthereumSigner
from safe_notification_service.ether.tests.factories import \
    get_eth_address_with_key

from ..models import Device, DevicePair
from ..serializers import isoformat_without_ms

faker = Faker()


class DeviceFactory(factory.DjangoModelFactory):
    push_token = factory.Faker('sha256', raw_output=False)
    owner = factory.LazyFunction(lambda: get_eth_address_with_key()[0])

    class Meta:
        model = Device


class DevicePairFactory(factory.DjangoModelFactory):
    authorizing_device = factory.SubFactory(DeviceFactory)
    authorized_device = factory.SubFactory(DeviceFactory)

    class Meta:
        model = DevicePair


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


def get_notification_mock_data(devices=None, eth_address_and_key: Tuple[str, str]= None):
    """ Generates a dictionary data specifying a notification message """
    message = json.dumps({'my_message': faker.name(), 'my_another_key': faker.name()})

    if eth_address_and_key:
        eth_address, eth_key = eth_address_and_key
    else:
        eth_address, eth_key = get_eth_address_with_key()

    if not devices:
        eth_address2, _ = get_eth_address_with_key()
        eth_address3, _ = get_eth_address_with_key()
        devices = [eth_address2, eth_address3]

    return {
        'devices': devices,
        'message': message,
        'signature': get_signature_json(message, eth_key),
    }


def get_google_billing_test_data() -> Tuple[str, str, str]:
    app_public_key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAm4w3ftcwdpqMMB4xTJJ/BNl9Ws6/vpJjAhDEaGPXZNO4CX0j9OtP/Ajl35QQIfQXnuLvkDislMYRTSsnLiOsP7FbZWxngKkMOteteknFuKLx2MXgWDbDVX2pzjCqSbHEXbo2zwpZ5vuaQilxgsYigBqobxw48thJvALfAmXBt/W57jc81jxzBOSNjWFLTGQa51Tv+eRCe30UAlRIOvQS1+I63n1nS1tLcVgcdBp/txdsrd2bHPWW0SIo5U1KPmWWXxA4wQ2WERIJQvOBJe2I11cGVsLiMuDshVmE1onpZDKSfF2gT4IvtM0lMRAfbdX5rmonz5Epf8on+EODlAf96wIDAQAB'
    purchase_json = '{"orderId":"GPA.3329-5458-1185-47553","packageName":"pm.gnosis.billingsample","productId":"gas","purchaseTime":1524652039139,"purchaseState":0,"purchaseToken":"nlhfgblkdihollmhcpkggkeo.AO-J1Oz1zkh_AogdW_xmXgsGC1pQ6Jl-nFI_SZ1cayDDI5lnKsZLyMwgjQkAMR39701mxGRhEiCSH9jhFKiL58M0HcV35tKSfE5gIKKxXcFAt9a_wmkpXnY"}'
    purchase_signature = 'bRlFfj2XTkwG5YX0MC1+JOBW0aJg8FwRqVYwieb9IpeO/tITqjgWYa9ZOx1xGHHC2A9aP+Db9r36nBvlq6K0qdBwBJRozwrPHRjc1kQNcMypCS1tHJCkv7A+GZHEVBIwsCK1kABTQHp2vIi2wDzvaR2r/EUZYevLPxcF5Y0gjzJH4A0zK7Hr8GorBbMKmtFwrhtheLrzqNrYVIwJ5sTAZvGvbH6Bva5f1uVJokgz4DE/04WmKIrczufXsc+CA4rve8oPvSs0eUW57Si0lIAHGyILpsw8F2whB2d71gyRj8qeWDQR8Rz0oaLpyOimNJq7pY0p3yyvn3+l3zYbGDfQog=='

    return app_public_key, purchase_json, purchase_signature
