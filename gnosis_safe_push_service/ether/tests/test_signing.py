from django.test import TestCase
from django.conf import settings
from ethereum import utils

from ..signing import EthereumSignedMessage
from .factories import get_eth_account_with_key


ETH_ACCOUNT, ETH_KEY = get_eth_account_with_key()
ETH_ACCOUNT_BAD_CHECKSUM = ETH_ACCOUNT.lower()


class TestSigning(TestCase):

    def test_ethereum_signed_message(self):
        prefix = settings.ETH_HASH_PREFIX
        message = "hello"
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
