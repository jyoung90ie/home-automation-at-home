import logging
from re import L

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.urls.base import reverse

from ..models import BaseAbstractModel
from .utils import Pushbullet

logger = logging.getLogger("mqtt")
logging.basicConfig(level=logging.INFO)


class NotificationMedium(models.TextChoices):
    """List of supported notification methods"""

    EMAIL = "Email"
    PUSHBULLET = "Pushbullet"


class NotificationSetting(BaseAbstractModel):
    """Stores all mediums by which a user should be notified"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    notification_medium = models.CharField(
        verbose_name="Notification channel",
        max_length=30,
        choices=NotificationMedium.choices,
        default=NotificationMedium.EMAIL,
    )
    is_enabled = models.BooleanField(
        verbose_name="Enable notifications", default=True)

    class Meta:
        """Only permit user to create one entry per notification method"""

        constraints = [
            UniqueConstraint(
                fields=["user", "notification_medium"], name="user_notification_medium"
            )
        ]

    def get_absolute_url(self):
        return reverse("notifications:list")

    def __str__(self) -> str:
        return self.notification_medium


class Notification(BaseAbstractModel):
    """Records all notifications sent to user including medium"""

    medium = models.ForeignKey(
        NotificationSetting, on_delete=models.SET_NULL, null=True, blank=False
    )
    topic = models.CharField(max_length=100, null=False, blank=False)
    message = models.TextField(blank=False, null=False)
    triggered_by = models.CharField(max_length=200, blank=False, null=False)


class PushbulletNotification(BaseAbstractModel):
    """Provider specific data fields"""

    notification = models.OneToOneField(
        NotificationSetting, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=60, null=False, blank=False)

    def send(self, topic, message, triggered_by, notification_obj):
        """Invoke functionality to send notification"""
        pushbullet = Pushbullet(access_token=self.access_token)

        logging.info(
            "Sending pushbullet notification (topic=%s, message=%s)", topic, message
        )

        # message += f"\n\nTriggered by: {triggered_by}"
        pushbullet.send_push(title=topic, body=message)

        # create notification record
        obj = Notification(
            medium=notification_obj,
            topic=topic,
            message=message,
            triggered_by=triggered_by,
        )
        obj.save()


class EmailNotification(BaseAbstractModel):
    """Specifies email notification settings"""

    notification = models.OneToOneField(
        NotificationSetting, on_delete=models.CASCADE)
    from_email = models.EmailField(null=False, blank=False)
    to_email = models.EmailField(null=False, blank=False)

    def send(self, topic, message, triggered_by, notification_obj):
        """Invoke functionality to send notification"""
        email = send_mail(
            subject=topic,
            message=message,
            from_email=self.from_email,
            recipient_list=[self.to_email],
            fail_silently=True,
        )

        if email:
            # create notification record
            logger.info("Email sent for trigger %s", triggered_by)
            obj = Notification(
                medium=notification_obj,
                topic=topic,
                message=message,
                triggered_by=triggered_by,
            )
            obj.save()
