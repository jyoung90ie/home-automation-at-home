"""Captures user device information which can be used to link to hardware devices via other
modules"""
import logging
from typing import TYPE_CHECKING, Dict, Union

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import EmptyResultSet, ObjectDoesNotExist
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..models import BaseAbstractModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

if TYPE_CHECKING:
    from ..zigbee.models import ZigbeeDevice, ZigbeeLog, ZigbeeMessage


class DeviceProtocol(models.TextChoices):
    """List of support smart device communication protocols"""

    API = "API", _("API")
    ZIGBEE = "ZIGBEE", _("Zigbee")


class DeviceLocationsQuerySet(models.QuerySet):
    """Custom queries"""

    def by_user(self, user):
        """Return device locations created by specified user"""
        return self.filter(user=user)

    def total_devices_by_protocol_and_location(
        self, location: "DeviceLocation", protocol: "DeviceProtocol"
    ):
        """Return total number of devices with specified protocol in the specified location"""
        return self.filter(device__protocol=protocol, device__location=location)

    def total_zigbee_by_location(self, location: "DeviceLocation"):
        """Return total zigbee devices in location"""
        return self.total_devices_by_protocol_and_location(
            location=location, protocol=DeviceProtocol.ZIGBEE
        ).count()

    def total_api_by_location(self, location: "DeviceLocation"):
        """Return total API devices in location"""
        return self.total_devices_by_protocol_and_location(
            location=location, protocol=DeviceProtocol.API
        ).count()


class DeviceLocationManager(models.Manager.from_queryset(DeviceLocationsQuerySet)):
    """Custom object manager"""


class DeviceLocation(BaseAbstractModel):
    """Permits users to define their own custom device locations"""

    objects = DeviceLocationManager()
    location = models.CharField(
        verbose_name="location name", max_length=100, blank=False, null=False
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "location"], name="user_device_location")
        ]

    def get_absolute_url(self):
        """Default redirect url for forms"""
        return reverse("devices:locations:detail", kwargs={"uuid": self.uuid})

    def __str__(self) -> str:
        return f"{self.location}"

    def save(self, *args, **kwargs):
        # save lowercase to prevent duplicates with different casing
        self.location = self.location.lower()

        super().save(*args, **kwargs)

    def get_linked_devices(self) -> Union["QuerySet", None]:
        linked_devices = None
        try:
            linked_devices = self.user.get_linked_devices

            if linked_devices:
                linked_devices = linked_devices.filter(location=self)
        except (EmptyResultSet, ObjectDoesNotExist):
            pass

        return linked_devices

    def total_linked_devices(self) -> int:
        """Return number of user's linked devices in specified location"""
        total = 0

        try:
            total = self.get_linked_devices().count()
        except TypeError:
            # queryset wasn't returned
            pass

        return total


class DeviceQuerySet(models.QuerySet):
    """Custom query set inherited by manager"""

    def get_event_triggers(self):
        """Return event triggers the object is assocaited with"""
        return self.filter(eventtrigger_set__is_enabled=True)


class DeviceManager(models.Manager.from_queryset(DeviceQuerySet)):
    """Customer object manager"""


class Device(BaseAbstractModel):
    """Base device model"""

    objects = DeviceManager()

    friendly_name = models.CharField(max_length=150, blank=False, null=False)
    device_identifier = models.CharField(max_length=255, blank=False, null=False)
    location = models.ForeignKey(DeviceLocation, on_delete=models.PROTECT)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    protocol = models.CharField(
        max_length=10,
        choices=DeviceProtocol.choices,
        default=DeviceProtocol.API,
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "device_identifier"], name="user_device_identifier"
            ),
            UniqueConstraint(
                fields=["user", "friendly_name"], name="user_device_friendly_name"
            ),
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.zigbee_model = apps.get_model("zigbee", "ZigbeeDevice")

    def save(self, link_devices=True, *args, **kwargs) -> None:
        # save lowercase to prevent duplicates with different casing
        self.friendly_name = self.friendly_name.lower()
        self.device_identifier = self.device_identifier.lower()

        super().save(*args, **kwargs)

        obj = self
        if not isinstance(self, Device):
            # if item is queryset get the object inside it
            obj = self.first()
        
        if link_devices:
            obj.try_to_link_zigbee_device()

    def get_zigbee_device(
        self, field_name: str = "zigbeedevice_set"
    ) -> Union["ZigbeeDevice", None]:
        """Return ZigbeeDevice object"""
        obj: "ZigbeeDevice" = getattr(self, field_name, None)
        return obj.first() if obj else None

    def get_zigbee_messages(
        self, latest_only: bool = False, field_name: str = "zigbeemessage_set"
    ) -> Union[QuerySet["ZigbeeMessage"], None]:
        """Return all raw messages for zigbee device"""
        zb_device: "ZigbeeDevice" = self.get_zigbee_device()

        messages = None

        if zb_device:
            if isinstance(zb_device, QuerySet):
                zb_device = zb_device.get()

            try:
                messages = getattr(zb_device, field_name).all()

                # if not messages:
                # return []

                if latest_only:
                    messages = [messages.order_by("-created_at").first()]
            except AttributeError as ex:
                logger.error("There was a problem aggregating ZigbeeMessages - %s", ex)

        return messages

    def get_zigbee_logs(
        self,
        filter_message: "ZigbeeMessage" = None,
        latest_only: bool = False,
        field_name: str = "zigbeelog_set",
    ) -> Union[QuerySet["ZigbeeLog"], None]:
        """
        Return all processed messages for zigbee device.
        If latest_only is True, returns only the most recent log entry based on created_at field.
        If filter_for_message is specified, returns logs that object ONLY.
        """
        logs = None
        zigbee_messages = self.get_zigbee_messages(latest_only=latest_only)

        if not zigbee_messages or len(zigbee_messages) == 0:
            logger.info("ZigbeeDevice has no messages - %s", self)
            return logs

        # loop through all messages
        logs = []
        for message in zigbee_messages:
            if filter_message and filter_message != message:
                # skip if message doesn't match when filter is applied
                continue

            try:
                logs_for_message = getattr(message, field_name).all()

                if latest_only:
                    # latest_only -> returns only latest ZigbeeMessage -> no need to build
                    # queryset of logs as only one result
                    return logs_for_message

                for log in logs_for_message:
                    logs.append(log)

            except AttributeError as ex:
                logs = None
                logger.error("There was a problem aggregating ZigbeeLogs - %s", ex)

        return logs

    def get_latest_zigbee_logs(self) -> Union[QuerySet["ZigbeeLog"], None]:
        """Returns the parsed logs eminating from the last ZigbeeMessage received"""
        return self.get_zigbee_logs(latest_only=True)

    def try_to_link_zigbee_device(self) -> None:
        """Filters ZigbeeDevice objects with device friendly_name and device_identifier to see if
        there are any unlinked matches - which will be then linked to the current device."""
        if self.protocol != DeviceProtocol.ZIGBEE or self.get_zigbee_device():
            logger.debug("Device already linked")
            return

        if not self.zigbee_model:
            logger.debug(
                "Cannot link zigbee device - ZigbeeDevice model has not been setup in __init__()"
            )
            return

        try:
            logger.info("Attempting to link device...")
            # not using Q model here as priority is on a hierarchical match - if using
            # Q, potential for two matches exists
            zigbee_device = self.zigbee_model.objects.filter(
                Q(ieee_address=self.device_identifier)
                | Q(friendly_name=self.friendly_name)
            )

            if zigbee_device and not hasattr(zigbee_device, "device"):
                # obj found and is not already matched
                zigbee_device = zigbee_device.first()

                zigbee_device.device = self
                zigbee_device.save()

                logger.info("Device linked - ZigbeeDevice obj= %s", zigbee_device)

        except (self.zigbee_model.DoesNotExist, Exception) as ex:
            logger.error("Device could not be linked - %s", ex)

    def get_linked_device(self, return_values=False) -> Union["ZigbeeDevice", None]:
        """Return the first hardware device that was linked to specified user device - returns
        only the first obj"""
        foreign_keys = ["zigbeedevice_set", "apidevice_set"]

        for fk_name in foreign_keys:
            fk_obj = getattr(self, fk_name, None)
            is_linked = fk_obj and hasattr(fk_obj.first(), "device")

            if is_linked:
                fk_obj = fk_obj.all().order_by(
                    "created_at"
                )  # return only first obj by creation date

                if return_values:
                    fk_obj = fk_obj.values()

                return fk_obj.first()

        return None

    def get_linked_device_values(self) -> dict:
        """Return dict containing key-value pairs representing data model field and value"""
        return self.get_linked_device(return_values=True)

    def is_linked(self) -> bool:
        """Returns true if user device is linked to a hardware device"""
        return self.get_linked_device() is not None

    def is_controllable(self) -> bool:
        """Returns true if the underlying hardware device can be controlled"""
        if self.is_linked:
            try:
                linked_device = self.get_linked_device()
                return getattr(linked_device, "is_controllable", False)
            except AttributeError as ex:
                pass
        return False

    def get_absolute_url(self):
        """Default redirect url"""
        return reverse("devices:device:detail", kwargs={"uuid": self.uuid})

    def last_communication(self) -> str:
        """Returns the date and time of the most recent communication from the hardware device"""
        received_at: str = ""
        try:
            last_message = self.get_zigbee_messages(latest_only=True)[0]
            received_at = last_message.created_at

        except Exception as ex:
            logger.info(ex)
            received_at = "-"

        return received_at

    def get_event_triggers(self) -> "QuerySet":
        """Return all enabled event triggers that object is related to"""
        return self.eventtrigger_set.filter(is_enabled=True)

    def __str__(self):
        return f"{self.friendly_name} [{self.device_identifier}]"


class DeviceState(BaseAbstractModel):
    """Stores device states that can be used to trigger the device to assume a particular
    state (e.g. on/off)"""

    device_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    device_object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey(
        "device_type", "device_object_id"
    )  # hardware device

    name = models.CharField(
        verbose_name="Name you want to save this state under",
        max_length=50,
        blank=False,
        null=False,
    )
    command = models.CharField(
        verbose_name="What is the command name that invokes the state change in your device?",
        max_length=100,
        blank=False,
    )
    command_value = models.CharField(
        verbose_name="What state value should be sent to your device?",
        max_length=100,
        blank=False,
    )

    def __str__(self) -> str:
        """String representation of object"""
        return f"{self.name} [{self.command} = {self.command_value}]"

    @property
    def friendly_name(self):
        """Returns friendly_name field from connected Device model"""
        return self.content_object.device.friendly_name

    @property
    def hardware_device_obj(self):
        """Returns connected hardware device model instance (e.g. ZigbeeDevice)"""
        return self.content_object

    @property
    def user_device_obj(self):
        """Returns connected user Device model instance"""
        return self.content_object.device

    def save(self, *args, **kwargs):
        # device will only recognise lowercase commands
        self.command = self.command.lower()
        self.command_value = self.command_value.lower()

        super().save(*args, **kwargs)
