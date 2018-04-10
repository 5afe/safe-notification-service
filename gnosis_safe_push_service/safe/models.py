from django.db import models
from model_utils.models import TimeStampedModel


class Device(TimeStampedModel):
    push_token = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='push_token'
    )
    owner = models.CharField(
        max_length=150,
        primary_key=True,
        verbose_name='onwer'
    )

    class Meta:
        verbose_name = 'device'
        verbose_name_plural = 'devices'

    def __str__(self):
        return self.push_token


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
        verbose_name = 'device pair'
        verbose_name_plural = 'device pairs'

    def __str__(self):
        return 'D1: %s, D2: %s' % (self.authorized_device.owner, self.authorizing_device.owner)
