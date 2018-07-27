from django.contrib import admin

from .models import Device, DevicePair


class DeviceAdmin(admin.ModelAdmin):
    fieldsets = (
        ('general_information', {
           'fields': ('push_token', 'owner',)
        }),
    )
    list_display = ('created', 'push_token', 'owner',)
    readonly_fields = ('created', 'modified')


class DevicePairAdmin(admin.ModelAdmin):
    fieldsets = (
        ('general_information', {
           'fields': ('authorizing_device', 'authorized_device',)
        }),
    )
    list_display = ('created', 'authorizing_device', 'authorized_device',)
    readonly_fields = ('created', 'modified')


admin.site.register(Device, DeviceAdmin)
admin.site.register(DevicePair, DevicePairAdmin)
