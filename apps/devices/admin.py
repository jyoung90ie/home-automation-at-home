"""Customises admin pages for device related models to display more useful fields"""
from django.contrib import admin

from . import models


class DeviceAdmin(admin.ModelAdmin):
    """Customises admin page for this model"""

    list_display = (
        "device_identifier",
        "friendly_name",
        "user",
        "created_at",
        "updated_at",
    )

    readonly_fields = ("uuid", "created_at", "updated_at")


class DeviceLocationAdmin(admin.ModelAdmin):
    """Customises admin page for this model"""

    list_display = (
        "location",
        "user",
        "created_at",
        "updated_at",
    )

    readonly_fields = ("uuid", "created_at", "updated_at")


class DeviceStateAdmin(admin.ModelAdmin):
    """ """


admin.site.register(models.Device, DeviceAdmin)
admin.site.register(models.DeviceLocation, DeviceLocationAdmin)
admin.site.register(models.DeviceState, DeviceStateAdmin)
