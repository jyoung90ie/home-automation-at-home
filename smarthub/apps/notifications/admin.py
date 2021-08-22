from django.contrib import admin

from . import models


class EmailInline(admin.TabularInline):
    model = models.EmailNotification
    extra = 0
    fields = ("from_email", "to_email")


class PushbulletInline(admin.TabularInline):
    model = models.PushbulletNotification
    extra = 0
    fields = ("access_token",)


class UserNotificationSettingAdmin(admin.ModelAdmin):
    list_display = (
        "notification_medium",
        "is_enabled",
        "created_at",
        "updated_at",
    )

    def get_inlines(self, request, obj):
        """Custom logic for displaying inlines dependent on notification medium"""
        inlines = []

        notification_medium = getattr(obj, "notification_medium")
        if notification_medium == models.NotificationMedium.EMAIL:
            inlines.append(EmailInline)
        elif notification_medium == models.NotificationMedium.PUSHBULLET:
            inlines.append(PushbulletInline)

        return inlines


class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "medium",
        "topic",
        "triggered_by",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )


admin.site.register(models.NotificationSetting, UserNotificationSettingAdmin)
admin.site.register(models.Notification, NotificationAdmin)
