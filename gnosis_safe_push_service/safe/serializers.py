from django.utils.functional import cached_property
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

    @cached_property
    def ethereum_signed_message(self) -> EthereumSignedMessage:
        v = self.initial_data['signature']['v']
        r = self.initial_data['signature']['r']
        s = self.initial_data['signature']['s']
        return EthereumSignedMessage(self.message, v, r, s)

    @property
    def hashed_fields(self):
        """
        :return: fields to concatenate for hash calculation
        :rtype: tuple(str)
        """
        return ()

    @property
    def message(self) -> bytes:
        return ''.join([self.initial_data[hashed_field] for hashed_field in self.hashed_fields])

    @property
    def message_hash(self) -> bytes:
        return self.ethereum_signed_message.message_hash

    @property
    def signing_address(self) -> str:
        return self.ethereum_signed_message.get_signing_address()

    def validate(self, data):
        if int(self.ethereum_signed_message.get_signing_address(), 16):
            return super().validate(data)
        else:  # 0x0 address
            raise ValidationError("Signed message is not valid, signer is ZERO address")


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
