from django.contrib import admin

from .models import Device, DevicePair, NotificationType


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('created', 'push_token', 'owner', 'client', 'version_name')
    list_filter = ('client', 'version_name')
    ordering = ['-created']
    readonly_fields = ('created', 'modified')
    search_fields = ['owner', 'push_token']


@admin.register(DevicePair)
class DevicePairAdmin(admin.ModelAdmin):
    list_display = ('created', 'authorizing_device', 'authorized_device',)
    readonly_fields = ('created', 'modified')
    search_fields = ['authorizing_device', 'authorized_device']


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'ios', 'android', 'web')
    list_filter = ('name', 'ios', 'android', 'web')
    search_fields = ['name', 'description']
