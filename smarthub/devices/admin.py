from django.contrib import admin
from django.contrib.admin.decorators import register
from . import models


class DeviceAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return (
            "device_identifier",
            "friendly_name",
            "user",
            "created_at",
            "updated_at",
        )


class DeviceLocationAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return (
            "location",
            "user",
            "created_at",
            "updated_at",
        )


admin.site.register(models.Device, DeviceAdmin)
admin.site.register(models.DeviceLocation, DeviceLocationAdmin)
