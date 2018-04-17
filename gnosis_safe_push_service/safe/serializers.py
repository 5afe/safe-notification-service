from typing import Any, Dict, Tuple

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from gnosis_safe_push_service.ether.signing import EthereumSignedMessage
from gnosis_safe_push_service.safe.models import Device, DevicePair


class SignatureSerializer(serializers.Serializer):
    v = serializers.IntegerField(min_value=0, max_value=30)
    r = serializers.IntegerField(min_value=0)
    s = serializers.IntegerField(min_value=0)


class SignedMessageSerializer(serializers.Serializer):
    """
    Inherit from this class and define get_hashed_fields function
    Take care not to define `message`, `message_hash` or `signing_address` fields
    """
    signature = SignatureSerializer()

    def validate(self, data):
        v = data['signature']['v']
        r = data['signature']['r']
        s = data['signature']['s']
        message = ''.join(self.get_hashed_fields(data))
        ethereum_signed_message = EthereumSignedMessage(message, v, r, s)
        data['message'] = message
        data['message_hash'] = ethereum_signed_message.message_hash
        data['signing_address'] = ethereum_signed_message.get_signing_address()
        return data

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        """
        :return: fields to concatenate for hash calculation
        :rtype: Tuple[str]
        """
        return ()


class AuthSerializer(SignedMessageSerializer):
    push_token = serializers.CharField()

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return data['push_token'],

    def create(self, validated_data):
        instance, _ = Device.objects.update_or_create(
            push_token=validated_data['push_token'],
            owner=validated_data['signing_address']
        )
        return instance


class TemporaryAuthorizationSerializer(SignedMessageSerializer):
    expiration_date = serializers.DateTimeField()
    connection_type = serializers.CharField()

    def validate_expiration_date(self, value):
        if timezone.now() > value:
            raise ValidationError("Exceeded expiration date")
        return value

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return data['expiration_date'].isoformat(), data['connection_type']


class PairingSerializer(SignedMessageSerializer):
    temporary_authorization = TemporaryAuthorizationSerializer()

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return data['temporary_authorization']['signing_address'],

    def create(self, validated_data):
        chrome_extension_address = validated_data['temporary_authorization']['signing_address']
        owner = validated_data['signing_address']

        chrome_device = Device.objects.get(owner=chrome_extension_address)
        owner_device = Device.objects.get(owner=owner)

        instance, _ = DevicePair.objects.update_or_create(
            authorizing_device=owner_device,
            authorized_device=chrome_device,
        )

        _, _ = DevicePair.objects.update_or_create(
            authorizing_device=chrome_device,
            authorized_device=owner_device,
        )

        return instance


class PairingDeletionSerializer(SignedMessageSerializer):
    device = serializers.CharField()

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return data['device']



