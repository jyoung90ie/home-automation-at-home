from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import BaseAbstractModel


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

    def get_absolute_url(self):
        return reverse("devices:device:detail", kwargs={"uuid": self.uuid})

    def __str__(self):
        return f"{self.friendly_name} [{self.device_identifier}]"
