from datetime import datetime
from typing import Any, Dict, Tuple
from ethereum.utils import checksum_encode

from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from gnosis_safe_push_service.ether.signing import EthereumSignedMessage
from gnosis_safe_push_service.safe.models import Device, DevicePair
from gnosis_safe_push_service.firebase.client import FirebaseClient


def isoformat_without_ms(date_time):
    return date_time.replace(microsecond=0).isoformat()


# ================================================ #
#                Base Serializers
# ================================================ #


class SignatureSerializer(serializers.Serializer):
    v = serializers.IntegerField(min_value=0, max_value=30)
    r = serializers.IntegerField(min_value=0)
    s = serializers.IntegerField(min_value=0)


# ================================================ #
#                Custom Fields
# ================================================ #
class EthereumAddressField(serializers.Field):
    """
    Ethereum address checksumed
    https://github.com/ethereum/EIPs/blob/master/EIPS/eip-55.md
    """

    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        # Check if address is valid

        try:
            if checksum_encode(data) != data:
                raise ValueError
        except ValueError:
            raise ValidationError("Address %s is not checksumed" % data)
        except Exception:
            raise ValidationError("Address %s is not valid" % data)

        return data


# ================================================ #
#                 Serializers
# ================================================ #
class SignedMessageSerializer(serializers.Serializer):
    """
    Inherit from this class and define get_hashed_fields function
    Take care not to define `message`, `message_hash` or `signing_address` fields
    """
    signature = SignatureSerializer()

    def validate(self, data):
        super().validate(data)
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
    expiration_date = serializers.CharField()

    def validate_expiration_date(self, value):
        # Format should be like '2018-04-20T08:18:36+00:00'
        datetime_format = '%Y-%m-%dT%H:%M:%S%z'

        try:
            if value[-3] == ':':
                value = value[:-3] + value[-2:]
            value = datetime.strptime(value, datetime_format)
        except ValueError:
            raise ValidationError("Date must be '{}' (like 2018-04-20T08:18:36+00:00)".format(datetime_format))

        if timezone.now() > value:
            raise ValidationError("Exceeded expiration date")
        return value

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return isoformat_without_ms(data['expiration_date'])


class PairingSerializer(SignedMessageSerializer):
    temporary_authorization = TemporaryAuthorizationSerializer()

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return data['temporary_authorization']['signing_address'],

    def validate(self, data):
        super().validate(data)

        if data['temporary_authorization']['signing_address'] == data['signing_address']:
            raise ValidationError('Both signing addresses must be different')

        return data

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


class NotificationSerializer(SignedMessageSerializer):
    devices = serializers.ListField(child=EthereumAddressField(), min_length=1)
    message = serializers.CharField()

    def validate(self, data):
        super().validate(data)
        devices = data['devices']
        if len(set(devices)) != len(devices):
            raise ValidationError("Duplicated addresses are forbidden")

        signing_address = data['signing_address']
        if signing_address in devices:
            raise ValidationError("Signing address cannot be in the destination addresses")

        return data

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return data['message']

    def create(self, validated_data):
        signer_address = validated_data['signing_address']
        devices = validated_data['devices']

        pairings = DevicePair.objects.filter(
            (Q(authorizing_device__owner__in=devices) & Q(authorized_device__owner=signer_address))
        )

        # Firebase client
        client = FirebaseClient(credentials=settings.FIREBASE_AUTH_CREDENTIALS)

        for pairing in pairings:
            # Send firebase notification
            client.send_message(validated_data['message'], pairing.authorizing.push_token)
