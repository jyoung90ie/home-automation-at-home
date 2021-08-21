"""Captures information relating to device event triggers"""
from django.contrib.auth import get_user_model
from django.db import models
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _

from ..devices.models import Device
from ..models import BaseAbstractModel


class Event(BaseAbstractModel):
    """Stores user defined events and notification messaging"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    description = models.CharField(
        verbose_name="Descriptive name for this event", max_length=200, blank=False
    )
    is_enabled = models.BooleanField(
        verbose_name="Enable event triggers?", default=True
    )
    send_notification = models.BooleanField(
        verbose_name="Send notifications when triggered?", default=True
    )
    notification_topic = models.CharField(
        verbose_name="Subject for message when event is triggered",
        max_length=200,
        null=True,
        blank=True,
    )
    notification_message = models.CharField(
        verbose_name="Message you will receive when event is triggered",
        max_length=500,
        null=True,
        blank=True,
    )

    def get_absolute_url(self):
        """Default redirect url"""
        return reverse("events:event:detail", kwargs={"uuid": self.uuid})

    def __str__(self):
        return self.description


class EventTriggerType(models.TextChoices):
    """Accepted conditional types used for triggering events"""

    LESS_THAN = "Less than", _("Less than")
    LESS_THAN_OR_EQUAL = "Less than or equal to", _("Less than or equal to")
    EQUAL = "Equal to", _("Equal to")
    GREATER_THAN_OR_EQUAL = "Greater than or equal to", _(
        "Greater than or equal to")
    GREATER_THAN = "Greater than", _("Greater than")
    NOT_EQUAL = "Not equal to", _("Not equal to")


class EventTrigger(BaseAbstractModel):
    """Stores potential event trigger values. Metadata values will be checked against
    device log tables"""

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    metadata_field = models.CharField(
        verbose_name="Data field for event trigger",
        max_length=255,
        null=True,
        blank=False,
    )
    metadata_trigger_value = models.CharField(
        verbose_name="Data field value for trigger",
        max_length=255,
        null=True,
        blank=False,
    )
    trigger_type = models.CharField(
        max_length=100, choices=EventTriggerType.choices, default=EventTriggerType.EQUAL
    )
    is_enabled = models.BooleanField(
        verbose_name="Enable this trigger?", default=True)
