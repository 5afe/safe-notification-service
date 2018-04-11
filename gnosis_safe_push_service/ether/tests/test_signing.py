from django.test import TestCase
from django.conf import settings
from ethereum import utils

from ..signing import EthereumSignedMessage, EthereumSigner
from .factories import get_eth_account_with_key

from faker import Faker


ETH_ACCOUNT, ETH_KEY = get_eth_account_with_key()
ETH_ACCOUNT_BAD_CHECKSUM = ETH_ACCOUNT.lower()

faker = Faker()


class TestSigning(TestCase):

    def test_ethereum_signer(self):
        message = faker.name()
        prefix = faker.name()
        ethereum_signer = EthereumSigner(message, ETH_KEY, hash_prefix=prefix)

        self.assertEqual(ethereum_signer.hash_prefix, prefix)
        self.assertEqual(ethereum_signer.message_hash, utils.sha3(prefix + message))
        self.assertEqual(ethereum_signer.get_signing_address(), ETH_ACCOUNT)
        self.assertTrue(ethereum_signer.check_signing_address(ETH_ACCOUNT_BAD_CHECKSUM))

    def test_ethereum_signed_message(self):
        prefix = settings.ETH_HASH_PREFIX
        message = faker.name()
        prefixed_message = prefix + message
        message_hash = utils.sha3(prefixed_message)
        v, r, s = utils.ecsign(message_hash, ETH_KEY)
        ethereum_signed_message = EthereumSignedMessage(message, v, r, s)

        self.assertTrue(ethereum_signed_message.check_message_hash(message))

        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT))
        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT.lower()))
        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT[2:]))
        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT_BAD_CHECKSUM))

        self.assertEqual(ethereum_signed_message.get_signing_address(), ETH_ACCOUNT)
        self.assertTrue(utils.check_checksum(ethereum_signed_message.get_signing_address()))
