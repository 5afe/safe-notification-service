import json
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from django.utils import timezone

import factory.fuzzy
from eth_account import Account
from factory.django import DjangoModelFactory
from faker import Faker

from safe_notification_service.ether.signing import EthereumSigner

from ..models import Device, DevicePair, DeviceTypeEnum, NotificationType
from ..serializers import isoformat_without_ms

faker = Faker()


class DeviceFactory(DjangoModelFactory):
    push_token = factory.Faker('sha256', raw_output=False)
    owner = factory.LazyFunction(lambda: Account.create().address)
    push_token = factory.fuzzy.FuzzyText(length=20)
    build_number = factory.fuzzy.FuzzyInteger(0, 2000)
    version_name = factory.Sequence(lambda x: f'1.0.{x}')
    client = DeviceTypeEnum.ANDROID.value
    bundle = factory.Faker('linux_platform_token')

    class Meta:
        model = Device


class DevicePairFactory(DjangoModelFactory):
    authorizing_device = factory.SubFactory(DeviceFactory)
    authorized_device = factory.SubFactory(DeviceFactory)

    class Meta:
        model = DevicePair


class NotificationTypeFactory(DjangoModelFactory):
    name = factory.Faker('name')
    description = factory.Faker('sentence')
    ios = None
    android = None
    extension = None

    class Meta:
        model = NotificationType


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


def get_pairing_mock_data(expiration_date: Optional[datetime] = None,
                          another_device_account: Optional[Account] = None,
                          device_account: Optional[Account] = None):
    """ Generates a dictionary data for pairing purposes """
    expiration_date = expiration_date or isoformat_without_ms((timezone.now() + timedelta(days=2)))
    another_device_account = another_device_account or Account.create()
    device_account = device_account or Account.create()

    return {
        "temporary_authorization": {
            "expiration_date": expiration_date,
            "signature": get_signature_json(expiration_date, another_device_account.key),
        },
        "signature":  get_signature_json(another_device_account.address, device_account.key)
    }


def get_notification_mock_data(devices: Optional[List[str]] = None, account: Optional[Account] = None,
                               message: Optional[str] = None):
    """ Generates a dictionary data specifying a notification message """
    message = message or json.dumps({'my_message': faker.name(), 'my_another_key': faker.name()})

    if not account:
        account = Account.create()

    if not devices:
        devices = [Account.create().address, Account.create().address]

    return {
        'devices': devices,
        'message': message,
        'signature': get_signature_json(message, account.key),
    }


def get_google_billing_test_data() -> Tuple[str, str, str]:
    app_public_key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAm4w3ftcwdpqMMB4xTJJ/BNl9Ws6/vpJjAhDEaGPXZNO4CX0j9OtP/Ajl35QQIfQXnuLvkDislMYRTSsnLiOsP7FbZWxngKkMOteteknFuKLx2MXgWDbDVX2pzjCqSbHEXbo2zwpZ5vuaQilxgsYigBqobxw48thJvALfAmXBt/W57jc81jxzBOSNjWFLTGQa51Tv+eRCe30UAlRIOvQS1+I63n1nS1tLcVgcdBp/txdsrd2bHPWW0SIo5U1KPmWWXxA4wQ2WERIJQvOBJe2I11cGVsLiMuDshVmE1onpZDKSfF2gT4IvtM0lMRAfbdX5rmonz5Epf8on+EODlAf96wIDAQAB'
    purchase_json = '{"orderId":"GPA.3329-5458-1185-47553","packageName":"pm.gnosis.billingsample","productId":"gas","purchaseTime":1524652039139,"purchaseState":0,"purchaseToken":"nlhfgblkdihollmhcpkggkeo.AO-J1Oz1zkh_AogdW_xmXgsGC1pQ6Jl-nFI_SZ1cayDDI5lnKsZLyMwgjQkAMR39701mxGRhEiCSH9jhFKiL58M0HcV35tKSfE5gIKKxXcFAt9a_wmkpXnY"}'
    purchase_signature = 'bRlFfj2XTkwG5YX0MC1+JOBW0aJg8FwRqVYwieb9IpeO/tITqjgWYa9ZOx1xGHHC2A9aP+Db9r36nBvlq6K0qdBwBJRozwrPHRjc1kQNcMypCS1tHJCkv7A+GZHEVBIwsCK1kABTQHp2vIi2wDzvaR2r/EUZYevLPxcF5Y0gjzJH4A0zK7Hr8GorBbMKmtFwrhtheLrzqNrYVIwJ5sTAZvGvbH6Bva5f1uVJokgz4DE/04WmKIrczufXsc+CA4rve8oPvSs0eUW57Si0lIAHGyILpsw8F2whB2d71gyRj8qeWDQR8Rz0oaLpyOimNJq7pY0p3yyvn3+l3zYbGDfQog=='

    return app_public_key, purchase_json, purchase_signature
