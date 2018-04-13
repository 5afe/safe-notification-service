from faker import Factory as FakerFactory
from faker import Faker

from gnosis_safe_push_service.ether.signing import EthereumSigner

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
