from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import BaseAbstractModel

import logging

logger = logging.getLogger(__name__)


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

    def get_zigbee_device(self):
        zigbee_device = False
        try:
            zigbee_device = self.zigbeedevice_set.get()
        except:
            pass
        return zigbee_device

    def try_to_link_zigbee_device(self):
        """Looks in Zigbee devices to see if there are any matches using friendly_name and device_identifier"""
        if not self.DeviceProtocol.ZIGBEE or self.get_zigbee_device():
            return

        if not self.zigbee_model:
            logger.warning(
                "Cannot link zigbee device - ZigbeeDevice model not set within Device model"
            )
            return

        try:
            zigbee_device = self.zigbee_model.objects.get(
                models.Q(friendly_name=self.friendly_name)
                | models.Q(ieee_address=self.device_identifier)
            )

            if zigbee_device and not zigbee_device.device:
                # obj found and is not already matched
                zigbee_device.device = self
                zigbee_device.save()
        except self.zigbee_model.DoesNotExist:
            pass

    def get_absolute_url(self):
        return reverse("devices:device:detail", kwargs={"uuid": self.uuid})

    def __str__(self):
        return f"{self.friendly_name} [{self.device_identifier}]"
