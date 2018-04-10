import hashlib
import random

from faker import Factory as FakerFactory
from faker import Faker

fakerFactory = FakerFactory.create()
faker = Faker()

signature_prefix = 'gno'


def get_push_token():
    nonce = str(random.random()).encode()
    return hashlib.sha256(nonce).hexdigest()


def get_signature(token):
    sign = (signature_prefix + token).encode()
    return hashlib.sha256(sign).hexdigest()
