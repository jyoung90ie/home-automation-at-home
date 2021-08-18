from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..devices.models import Device
from ..models import BaseAbstractModel


class Event(BaseAbstractModel):
    """Stores user defined events and notification messaging"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    description = models.CharField(max_length=200, blank=False)
    is_enabled = models.BooleanField(default=True)
    send_notification = models.BooleanField(default=True)
    notification_topic = models.CharField(max_length=200)
    notification_message = models.CharField(max_length=500)


class EventTriggerType(models.TextChoices):
    """Accepted conditional types used for triggering events"""

    LESS_THAN = "Less than", _("Less than")
    LESS_THAN_OR_EQUAL = "Less than or equal to", _("Less than or equal to")
    EQUAL = "Equal to", _("Equal to")
    GREATER_THAN_OR_EQUAL = "Greater than or equal to", _("Greater than or equal to")
    GREATER_THAN = "Greater than", _("Greater than")
    NOT_EQUAL = "Not equal to", _("Not equal to")


class EventTrigger(BaseAbstractModel):
    """Stores potential event trigger values. Metadata values will be checked against device log tables"""

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    metadata_field = models.CharField(max_length=255, null=True, blank=False)
    metadata_trigger_value = models.CharField(max_length=255, null=True, blank=False)
    trigger_type = models.CharField(
        max_length=100, choices=EventTriggerType.choices, default=EventTriggerType.EQUAL
    )
    is_enabled = models.BooleanField(default=True)
