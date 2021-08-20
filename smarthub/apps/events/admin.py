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

        inlines = [EventTriggerInline]

        return inlines


admin.site.register(models.Event, EventAdmin)
