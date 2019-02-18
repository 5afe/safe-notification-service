from django.contrib import admin

from .models import Device, DevicePair, NotificationType


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    fieldsets = (
        ('general_information', {
           'fields': ('push_token', 'owner',)
        }),
    )
    list_display = ('created', 'push_token', 'owner',)
    readonly_fields = ('created', 'modified')


@admin.register(DevicePair)
class DevicePairAdmin(admin.ModelAdmin):
    fieldsets = (
        ('general_information', {
           'fields': ('authorizing_device', 'authorized_device',)
        }),
    )
    list_display = ('created', 'authorizing_device', 'authorized_device',)
    readonly_fields = ('created', 'modified')


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'ios', 'android', 'web')
