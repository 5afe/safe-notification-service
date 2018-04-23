from django.db import models
from model_utils.models import TimeStampedModel

from .validators import validate_checksumed_address


class Device(TimeStampedModel):
    push_token = models.TextField(
        verbose_name='push_token'
    )
    owner = models.CharField(
        max_length=42,
        primary_key=True,
        verbose_name='owner',
        validators=[validate_checksumed_address],
    )

    class Meta:
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'

    def __str__(self):
        return '{} - {}...'.format(self.owner, self.push_token[:10])


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
        return 'D1: %s, D2: %s' % (self.authorized_device.owner, self.authorizing_device.owner)
