from enum import Enum
from typing import List

from django.db import models

from model_utils.models import TimeStampedModel

from gnosis.eth.django.models import EthereumAddressField


class DeviceTypeEnum(Enum):
    ANDROID = 0
    IOS = 1
    EXTENSION = 2


class DeviceManager(models.Manager):
    def get_or_create_without_push_token(self, owner):
        try:
            return self.get(owner=owner)
        except self.model.DoesNotExist:
            return self.create(owner=owner, push_token=None)


class Device(TimeStampedModel):
    objects = DeviceManager()
    owner = EthereumAddressField(primary_key=True)
    push_token = models.TextField(null=True, blank=True)
    build_number = models.PositiveIntegerField(default=0)  # e.g. 1644
    version_name = models.CharField(max_length=100, default='')  # e.g 1.0.0
    client = models.PositiveSmallIntegerField(null=True, default=None,
                                              choices=[(tag.value, tag.name) for tag in DeviceTypeEnum])
    bundle = models.CharField(max_length=100, default='')

    class Meta:
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'

    def __str__(self):
        token = self.push_token[:10] if self.push_token else 'No Token'
        return '{} - {}...'.format(self.owner, token)

    def get_device_type(self):
        if self.device_type is None:
            return None
        else:
            return DeviceTypeEnum(self.get_device_type())


class DevicePair(TimeStampedModel):
    authorizing_device = models.ForeignKey(
        Device,
        related_name='authorizing_devices',
        on_delete=models.CASCADE
    )
    authorized_device = models.ForeignKey(
        Device,
        related_name='authorized_devices',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (('authorizing_device', 'authorized_device'),)
        verbose_name = 'Device Pair'
        verbose_name_plural = 'Device Pairs'

    def __str__(self):
        return '{} authorizes {}'.format(self.authorizing_device.owner, self.authorized_device.owner)


class NotificationType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    ios = models.BooleanField(default=False)
    android = models.BooleanField(default=True)
    extension = models.BooleanField(default=True)

    @property
    def enabled_device_types(self) -> List[DeviceTypeEnum]:
        device_types = []
        if self.ios:
            device_types.append(DeviceTypeEnum.IOS)
        if self.android:
            device_types.append(DeviceTypeEnum.ANDROID)
        if self.extension:
            device_types.append(DeviceTypeEnum.EXTENSION)
        return device_types
