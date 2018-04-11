from faker import Factory as FakerFactory
from faker import Faker

from gnosis_safe_push_service.ether.signing import EthereumSigner
from gnosis_safe_push_service.ether.tests.factories import get_eth_account_with_key


fakerFactory = FakerFactory.create()
faker = Faker()

ETH_ACCOUNT, ETH_KEY = get_eth_account_with_key()


def get_push_token():
    return faker.name()


def get_signature(message):
    ethereum_signer = EthereumSigner(message, ETH_KEY)
    v, r, s = ethereum_signer.v, ethereum_signer.r, ethereum_signer.s

    return {
        'v': v,
        'r': r,
        's': s
    }
