from django.contrib import admin
from .models import Device, DevicePair


class DeviceAdmin(admin.ModelAdmin):
    fieldsets = (
        ('general_information', {
           'fields': ('push_token', 'owner',)
        }),
    )
    list_display = ('push_token', 'owner',)


class DevicePairAdmin(admin.ModelAdmin):
    fieldsets = (
        ('general_information', {
           'fields': ('authorizing_device', 'authorized_device',)
        }),
    )
    list_display = ('authorizing_device', 'authorized_device',)


admin.site.register(Device, DeviceAdmin)
admin.site.register(DevicePair, DevicePairAdmin)