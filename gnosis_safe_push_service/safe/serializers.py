# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Device
import logging


infoLogger = logging.getLogger('infoLogger')
errorLogger = logging.getLogger('errorLogger')


class AuthSerializer(serializers.Serializer):
    """

    """
    push_token = serializers.CharField()
    signature = serializers.CharField()

    def validate_signature(self, value):
        # TODO validation
        # raise ValidationError(['Bad signature'])
        return value

    def get_owner(self, signature):
        # TODO include signature recovery
        return '0x' # TODO change

    def create(self, validated_data):
        owner = self.get_owner(validated_data.get('signature'))

        instance, created = Device.objects.update_or_create(
            push_token=validated_data.get('push_token'),
            owner=owner
        )
        return instance