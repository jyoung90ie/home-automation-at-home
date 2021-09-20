from django.contrib import admin
from django.contrib.contenttypes.admin import GenericInlineModelAdmin

from django_admin_inline_paginator.admin import TabularInlinePaginated

from ..devices.models import DeviceState
from . import models


def truncate_string(string_val, length=50):
    """Truncate string and append '...'"""
    if isinstance(string_val, str):
        original_length = len(string_val)
        string_val = string_val[:length]

        if len(string_val) < original_length:
            string_val += "..."
    return string_val


class ZigbeeMessageInline(TabularInlinePaginated):
    model = models.ZigbeeMessage
    per_page = 5
    extra = 0
    ordering = ["-created_at"]
    fields = ("topic", "raw_message")
    readonly_fields = ("created_at", "updated_at")


class ZigbeeLogsInline(TabularInlinePaginated):
    model = models.ZigbeeLog
    extra = 0
    per_page = 15
    ordering = ["-created_at"]
    readonly_fields = ("created_at", "updated_at")


class ZigbeeDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "friendly_name",
        "ieee_address",
        "vendor",
        "truncated_description",
        "device_owner",
        "created_at",
        "updated_at",
    )
    inlines = [
        ZigbeeMessageInline,
    ]
    readonly_fields = ("created_at", "updated_at")

    def device_owner(self, obj):
        """Return user object value"""
        return getattr(obj.device, "user", "N/A")

    def truncated_description(self, obj):
        """Return shortened device description"""
        return truncate_string(obj.description)


class ZigbeeMessageAdmin(admin.ModelAdmin):
    list_display = ("topic", "truncated_raw_message", "created_at")
    list_filter = ("topic",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [
        ZigbeeLogsInline,
    ]

    def truncated_raw_message(self, obj):
        """Return shortened device description"""
        return truncate_string(obj.raw_message, 100)


class ZigbeeLogAdmin(admin.ModelAdmin):
    list_display = (
        "broker_message",
        "metadata_type",
        "truncated_metadata_value",
        "created_at",
    )
    list_filter = ("broker_message__topic", "metadata_type")
    readonly_fields = ("created_at", "updated_at")

    def truncated_metadata_value(self, obj):
        return truncate_string(obj.metadata_value, 40)


admin.site.register(models.ZigbeeDevice, ZigbeeDeviceAdmin)
admin.site.register(models.ZigbeeMessage, ZigbeeMessageAdmin)
admin.site.register(models.ZigbeeLog, ZigbeeLogAdmin)
