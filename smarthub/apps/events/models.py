"""Captures information relating to device event triggers"""
import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _

from ..devices.models import Device
from ..models import BaseAbstractModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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

    def is_triggered(self, device_value) -> bool:
        """Compare device value to trigger value using trigger_type for comparison - returns bool
        True    -> trigger criteria has been met
        False   -> trigger criteria has not been met"""
        logger.info("Start EventTrigger is_triggered()")
        trigger_type = self.trigger_type
        trigger_value = self.metadata_trigger_value

        # convert all values to lower case
        trigger_value = (
            trigger_value.lower() if isinstance(trigger_value, str) else trigger_value
        )
        device_value = (
            device_value.lower() if isinstance(device_value, str) else device_value
        )

        if trigger_type == EventTriggerType.EQUAL:
            return trigger_value == device_value
        elif trigger_type == EventTriggerType.NOT_EQUAL:
            return trigger_value != device_value

        # next set of conditions require number - if not a number return false
        try:
            trigger_value = (
                int(trigger_value)
                if int(trigger_value) == float(trigger_value)
                else float(trigger_value)
            )
        except ValueError:
            return False

        if trigger_type == EventTriggerType.GREATER_THAN_OR_EQUAL:
            return device_value >= trigger_value
        elif trigger_type == EventTriggerType.GREATER_THAN:
            return device_value > trigger_value
        elif trigger_type == EventTriggerType.LESS_THAN:
            return device_value < trigger_value
        elif trigger_type == EventTriggerType.LESS_THAN_OR_EQUAL:
            return device_value <= trigger_value

        logger.info("Finish EventTrigger is_triggered()")

    def __str__(self) -> str:
        return f"Trigger Settings [Device={self.device} - Field={self.metadata_field} - Type={self.trigger_type} - Value={self.metadata_trigger_value}]"
