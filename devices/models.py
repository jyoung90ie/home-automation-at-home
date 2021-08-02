from django.db import models


class DeviceQuerySet(models.QuerySet):
    pass


class DeviceManager(models.Manager.from_queryset(DeviceQuerySet)):
    pass


# Create your models here.
class Device(models.Model):
    """Base device model"""

    objects = DeviceManager()

    name = models.CharField(max_length=150, blank=False, null=False)
    # location = models.CharField()
    # user =
