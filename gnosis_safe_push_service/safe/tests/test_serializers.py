from django.test import TestCase
from rest_framework.exceptions import ValidationError

from gnosis_safe_push_service.ether.signing import EthereumSignedMessage

from ..serializers import AuthSerializer
from .factories import (ETH_ACCOUNT, get_bad_signature, get_push_token,
                        get_signature)


class TestSerializers(TestCase):
    def test_auth_serializer(self):
        push_token = get_push_token()
        signature = get_signature(push_token)
        auth_data = {
            'push_token': push_token,
            'signature': signature
        }

        ethereum_signed_message = EthereumSignedMessage(push_token, signature['v'], signature['r'], signature['s'])

        push_token_hash = ethereum_signed_message.message_hash

        auth_serializer = AuthSerializer(data=auth_data)

        self.assertTrue(auth_serializer.is_valid())

        self.assertEqual(auth_serializer.message_hash, push_token_hash)

        self.assertTrue(auth_serializer.ethereum_signed_message.check_message_hash(push_token))

        self.assertEqual(auth_serializer.signing_address, ETH_ACCOUNT)

        bad_auth_data = {
            'push_token': push_token,
            'signature': get_bad_signature(push_token)
        }

        auth_serializer = AuthSerializer(data=bad_auth_data)

        self.assertRaises(ValidationError, auth_serializer.is_valid, raise_exception=True)
