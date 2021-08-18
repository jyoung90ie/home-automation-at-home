from django.contrib import admin

from . import models


class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_identifier",
        "friendly_name",
        "user",
        "created_at",
        "updated_at",
    )

    readonly_fields = ("uuid", "created_at", "updated_at")


class DeviceLocationAdmin(admin.ModelAdmin):
    list_display = (
        "location",
        "user",
        "created_at",
        "updated_at",
    )

    readonly_fields = ("uuid", "created_at", "updated_at")


admin.site.register(models.Device, DeviceAdmin)
admin.site.register(models.DeviceLocation, DeviceLocationAdmin)
