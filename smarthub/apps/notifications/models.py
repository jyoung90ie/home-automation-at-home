from re import L
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.constraints import UniqueConstraint

from ..models import BaseAbstractModel


class NotificationMediums(models.TextChoices):
    """List of supported notification methods"""

    EMAIL = "Email"
    PUSHBULLET = "Pushbullet"


class UserNotificationSetting(BaseAbstractModel):
    """Stores all mediums by which a user should be notified"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    notification_medium = models.CharField(
        max_length=30,
        choices=NotificationMediums.choices,
        default=NotificationMediums.EMAIL,
    )
    is_enabled = models.BooleanField(verbose_name="Enable notifications", default=True)

    class Meta:
        """Only permit user to create one entry per notification method"""

        constraints = [
            UniqueConstraint(
                fields=["user", "notification_medium"], name="user_notification_medium"
            )
        ]


class Notification(BaseAbstractModel):
    """Records all notifications sent to user including medium"""

    medium = models.ForeignKey(
        UserNotificationSetting, on_delete=models.SET_NULL, null=True, blank=False
    )
    topic = models.CharField(max_length=100, null=False, blank=False)
    message = models.TextField(blank=False, null=False)
    triggered_by = models.CharField(max_length=200, blank=False, null=False)


class PushbulletNotification(BaseAbstractModel):
    """Provider specific data fields"""

    notification = models.OneToOneField(
        UserNotificationSetting, on_delete=models.CASCADE
    )
    access_token = models.CharField(max_length=60, null=False, blank=False)


class EmailNotification(BaseAbstractModel):
    """Specifies email notification settings"""

    notification = models.OneToOneField(
        UserNotificationSetting, on_delete=models.CASCADE
    )
    from_email = models.EmailField(null=False, blank=False)
    to_email = models.EmailField(null=False, blank=False)
