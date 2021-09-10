"""Customises admin pages for device related models to display more useful fields"""
from django.contrib import admin

from . import models


class EventTriggerInline(admin.TabularInline):
    """Attach event triggers directly to related event object"""

    model = models.EventTrigger
    extra = 0
    fields = (
        "device",
        "metadata_field",
        "metadata_trigger_value",
        "trigger_type",
        "is_enabled",
    )
    readonly_fields = ("created_at", "updated_at")


class EventResponseInline(admin.TabularInline):
    """Attach event triggers directly to related event object"""

    model = models.EventResponse
    extra = 0
    fields = (
        "device_state",
        "device",
        "is_enabled",
    )
    readonly_fields = ("device_name", "created_at", "updated_at")


class EventAdmin(admin.ModelAdmin):
    """Display event model in admin"""

    list_display = (
        "user",
        "description",
        "is_enabled",
        "send_notification",
    )
    readonly_fields = ("created_at", "updated_at")

    def get_inlines(self, request, obj):
        """Custom logic for displaying inlines"""

        inlines = [EventTriggerInline, EventResponseInline]

        return inlines


class EventTriggerLogAdmin(admin.ModelAdmin):
    """Display event model in admin"""

    list_display = (
        "trunucate_event",
        "user",
        "triggered_by",
        "response_command",
        "created_at",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    def trunucate_event(self, obj):
        event = str(obj.event)
        truncated_event = event[:30]
        truncated_event = (
            f"{truncated_event}..." if len(event) > 30 else truncated_event
        )
        return truncated_event

    def user(self, obj):
        """Get user email to make it easier to identify logs"""
        return getattr(obj.event, "user", "")


admin.site.register(models.Event, EventAdmin)
admin.site.register(models.EventTriggerLog, EventTriggerLogAdmin)
