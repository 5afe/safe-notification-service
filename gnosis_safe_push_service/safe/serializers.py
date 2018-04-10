from ethereum.utils import sha3
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from gnosis_safe_push_service.ether.signing import EthereumSignedMessage

from .models import Device


class SignatureSerializer(serializers.Serializer):
    v = serializers.IntegerField(min_value=0, max_value=30)
    r = serializers.IntegerField(min_value=0)
    s = serializers.IntegerField(min_value=0)


class SignedMessageSerializer(serializers.Serializer):
    """
    Inherit from this class and define hashed_fields property
    """
    signature = SignatureSerializer()

    @property
    def hashed_fields(self):
        """
        :return: fields to concatenate for hash calculation
        :rtype: tuple(str)
        """
        return ()

    @property
    def signing_address(self) -> str:
        return self.ethereum_signed_message.get_signing_address()

    @property
    def ethereum_signed_message(self) -> EthereumSignedMessage:
        v = self.validated_data['signature']['v']
        r = self.validated_data['signature']['r']
        s = self.validated_data['signature']['s']
        return EthereumSignedMessage(self.message_hash, v, r, s)

    @property
    def message_hash(self) -> bytes:
        return sha3(''.join([self.validated_data[hashed_field] for hashed_field in self.hashed_fields]))


class AuthSerializer(SignedMessageSerializer):
    push_token = serializers.CharField()

    @property
    def hashed_fields(self):
        return 'push_token',

    def create(self, validated_data):
        owner = self.signing_address

        instance, _ = Device.objects.update_or_create(
            push_token=validated_data['push_token'],
            owner=owner
        )
        return instance
