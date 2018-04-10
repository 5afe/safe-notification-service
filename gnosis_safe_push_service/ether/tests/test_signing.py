from django.test import TestCase
from ethereum import utils

from ..signing import EthereumSignedMessage

# from django.conf import settings


ETH_ACCOUNT = '0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1'
ETH_ACCOUNT_BAD_CHECKSUM = '0x90f8bf6A479f320ead074411a4B0e7944Ea8c9C1'
ETH_KEY = bytes.fromhex('4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d')


class TestSigning(TestCase):

    def test_ethereum_signed_message(self):
        prefix = "gno"
        message = "hello"
        prefixed_message = prefix + message
        message_hash = utils.sha3(prefixed_message)
        v, r, s = utils.ecsign(message_hash, ETH_KEY)
        ethereum_signed_message = EthereumSignedMessage(message_hash, v, r, s)

        self.assertTrue(ethereum_signed_message.check_message_hash(message))

        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT))
        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT.lower()))
        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT[2:]))
        self.assertTrue(ethereum_signed_message.check_signing_address(ETH_ACCOUNT_BAD_CHECKSUM))

        self.assertEqual(ethereum_signed_message.get_signing_address(), ETH_ACCOUNT)
        self.assertTrue(utils.check_checksum(ethereum_signed_message.get_signing_address()))
