from django.db import models
from model_utils.models import TimeStampedModel

from .validators import validate_checksumed_address


class DeviceManager(models.Manager):
    def get_or_create_without_push_token(self, owner):
        try:
            return self.get(owner=owner)
        except self.model.DoesNotExist:
            return self.create(owner=owner, push_token=None)


class Device(TimeStampedModel):
    objects = DeviceManager()
    push_token = models.TextField(
        null=True,
        blank=True,
    )
    owner = models.CharField(
        max_length=42,
        primary_key=True,
        validators=[validate_checksumed_address],
    )

    class Meta:
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'

    def __str__(self):
        token = self.push_token[:10] if self.push_token else 'No Token'
        return '{} - {}...'.format(self.owner, token)


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
