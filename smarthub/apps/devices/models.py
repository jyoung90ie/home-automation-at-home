from typing import Union, TYPE_CHECKING
from django.db.models.constraints import UniqueConstraint
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import BaseAbstractModel

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..zigbee.models import ZigbeeDevice, ZigbeeLog, ZigbeeMessage


class DeviceLocationsQuerySet(models.QuerySet):
    """ """

    def by_user(self, user):
        return self.filter(user=user)


class DeviceLocationManager(models.Manager.from_queryset(DeviceLocationsQuerySet)):
    """ """


class DeviceLocation(BaseAbstractModel):
    """Permits users to define their own custom device locations"""

    objects = DeviceLocationManager()
    location = models.CharField(max_length=100, blank=False, null=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse("devices:locations:list")

    def __str__(self) -> str:
        return f"{self.location}"


class DeviceQuerySet(models.QuerySet):
    """ """


class DeviceManager(models.Manager.from_queryset(DeviceQuerySet)):
    """ """


class Device(BaseAbstractModel):
    """Base device model"""

    objects = DeviceManager()

    class DeviceProtocol(models.TextChoices):
        """List of support smart device communication protocols"""

        API = "API", _("API")
        ZIGBEE = "ZIGBEE", _("Zigbee")

    friendly_name = models.CharField(max_length=150, blank=False, null=False)
    device_identifier = models.CharField(max_length=255, blank=False, null=False)
    location = models.ForeignKey(DeviceLocation, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    protocol = models.CharField(
        max_length=10,
        choices=DeviceProtocol.choices,
        default=DeviceProtocol.API,
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "device_identifier"], name="user_device")
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.zigbee_model = apps.get_model("zigbee", "ZigbeeDevice")

    def save(self, *args, **kwargs):
        self.try_to_link_zigbee_device()
        return super().save(*args, **kwargs)

    def get_zigbee_device(
        self, field_name="zigbeedevice_set"
    ) -> Union[QuerySet["ZigbeeDevice"], bool]:
        """Return ZigbeeDevice object or false"""
        obj: "ZigbeeDevice" = getattr(self, field_name, False)

        return obj.all() if obj else False

    def get_zigbee_messages(
        self, latest_only=False, field_name="zigbeemessage_set"
    ) -> Union[QuerySet["ZigbeeMessage"], bool]:
        """Return all raw messages for zigbee device"""
        messages = False
        zb_device: "ZigbeeDevice" = self.get_zigbee_device()

        if zb_device:
            if isinstance(zb_device, QuerySet):
                zb_device = zb_device.get()

            try:
                messages = getattr(zb_device, field_name).all()

                if latest_only:
                    messages = [messages.order_by("-created_at").first()]
            except AttributeError:
                logger.error("There was a problem aggregating ZigbeeMessages")
                pass

        return messages

    def get_zigbee_logs(
        self, message_obj=None, latest_only=False, field_name="zigbeelog_set"
    ) -> Union[QuerySet["ZigbeeLog"], bool]:
        """
        Return all processed messages for zigbee device.
        If message_obj is specified, returns logs for specified message_obj ONLY.
        """
        messages = self.get_zigbee_messages(latest_only)

        if not messages:
            logger.info(f"ZigbeeDevice has no messages - {self}")
            return False

        if message_obj:
            if not isinstance(message_obj, apps.get_model("zigbee", "ZigbeeMessage")):
                logger.info(
                    "get_zigbee_logs(): Invalid object type provided - expected ZigbeeMessage (value={message_obj}"
                )
                return False
            return messages.filter(message=message_obj)

        logs = []

        for message in messages:
            try:
                message_logs = getattr(message, field_name).all()

                if latest_only:
                    # latest_only -> returns only latest ZigbeeMessage -> no need to build queryset of logs as only one result
                    return message_logs

                logs.append(message_logs)
            except AttributeError:
                logger.error("There was a problem aggregating ZigbeeLogs")
                pass

        return logs

    def get_lastest_zigbee_logs(self):
        return self.get_zigbee_logs(latest_only=True)

    def try_to_link_zigbee_device(self) -> None:
        """Looks in Zigbee devices to see if there are any matches using friendly_name and device_identifier"""
        if not self.DeviceProtocol.ZIGBEE or self.get_zigbee_device():
            return

        if not self.zigbee_model:
            logger.debug(
                "Cannot link zigbee device - ZigbeeDevice model not set within Device model"
            )
            return

        try:
            # not using Q model here as priority is on a hierarchical match - if using Q, potential for two matches exists
            zigbee_device = self.zigbee_model.objects.filter(
                ieee_address=self.device_identifier
            ) or self.zigbee_model.objects.filter(friendly_name=self.friendly_name)

            if zigbee_device and not zigbee_device.device:
                # obj found and is not already matched
                zigbee_device.device = self
                zigbee_device.save()
        except self.zigbee_model.DoesNotExist:
            pass

    def is_linked(self) -> bool:
        """Returns true if user device is linked to a hardware device"""
        fk_obj: "ZigbeeDevice"
        is_linked = False

        foreign_keys = ["zigbeedevice_set", "apidevice_set"]
        for fk_name in foreign_keys:
            if is_linked:
                break

            fk_obj = getattr(self, fk_name, False)
            is_linked = fk_obj and hasattr(fk_obj.first(), "device")

        return is_linked

    def get_absolute_url(self):
        return reverse("devices:device:detail", kwargs={"uuid": self.uuid})

    def __str__(self):
        return f"{self.friendly_name} [{self.device_identifier}]"
