import json
import logging
from datetime import datetime
from typing import Any, Dict, Tuple

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from ethereum.utils import checksum_encode
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from safe_notification_service.ether.signing import EthereumSignedMessage
from safe_notification_service.safe.models import Device, DevicePair
from safe_notification_service.safe.tasks import send_notification

from .helpers import validate_google_billing_purchase

logger = logging.getLogger(__name__)


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
    push_token = serializers.CharField(min_length=1)

    def get_hashed_fields(self, data: Dict[str, Any]) -> Tuple[str]:
        return data['push_token'],

    def validate_push_token(self, value):
        try:
            Device.objects.get(push_token=value)
            raise ValidationError('Push token %s already in use' % value)
        except Device.DoesNotExist:
            return value

    def create(self, validated_data):
        owner = validated_data['signing_address']
        push_token = validated_data['push_token']
        try:
            device = Device.objects.get(owner=owner)
            device.push_token = push_token
            device.save()
        except Device.DoesNotExist:
            device = Device.objects.create(
                owner=owner,
                push_token=push_token
            )
        return device


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

        chrome_device = Device.objects.get_or_create_without_push_token(chrome_extension_address)
        owner_device = Device.objects.get_or_create_without_push_token(owner)

        # Do pairing
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

    def validate_message(self, data):
        try:
            json.loads(data)
        except json.JSONDecodeError:
            raise ValidationError("Message must be a valid stringified JSON")
        return data

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
        """
        Takes care of getting the valid device pairs for the signing user and
        sends the notifications.
        """
        signer_address = validated_data['signing_address']
        devices = validated_data['devices']
        # convert message to JSON
        message = json.loads(validated_data['message'])

        pairings = DevicePair.objects.filter(
            (Q(authorizing_device__owner__in=devices) & Q(authorized_device__owner=signer_address))
        ).select_related('authorizing_device')

        logger.info('Found %s paired devices, sender: %s, devices: %s' % (pairings.count(), signer_address, devices))

        for pairing in pairings:
            # Call celery task for sending notification
            if pairing.authorizing_device.push_token:
                send_notification.delay(message, pairing.authorizing_device.push_token)
            else:
                logger.warning("Address %s has no push_token", pairing.authorizing_device.owner)

        return pairings

    def to_representation(self, instance):
        return {}


class GoogleInAppPurchaseSerializer(serializers.Serializer):
    signed_data = serializers.CharField(min_length=1)
    signature = serializers.CharField(min_length=344, max_length=344)

    def validate_signed_data(self, value):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError('Cannot decode signed_data JSON')

    def validate(self, data):
        signed_data_str = self.initial_data['signed_data']
        signed_data = data['signed_data']
        signature = data['signature']

        google_billing_public_key_base64 = settings.GOOGLE_BILLING_PUBLIC_KEY_BASE64

        if not google_billing_public_key_base64:
            raise ValidationError('GOOGLE_BILLING_PUBLIC_KEY_BASE64 environment variable not found')

        if not validate_google_billing_purchase(google_billing_public_key_base64, signed_data_str, signature):
            raise ValidationError('Cannot validate google signed data')

        data['order_id'] = signed_data['orderId']
        data['product_id'] = signed_data['productId']
        data['purchase_time'] = datetime.utcfromtimestamp(signed_data['purchaseTime'] / 1000)
        data['package_name'] = signed_data['packageName']

        return data
