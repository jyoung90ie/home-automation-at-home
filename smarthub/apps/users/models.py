"""Custom user model implementation"""
from django.apps import apps
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from . import defines


class CustomUserManager(BaseUserManager):
    """Custom implementation for creating users with email as username"""

    def create_user(self, email, password, **extra_fields):
        """Overrides default to user email as username"""
        if not email:
            raise ValueError(_("Email address must be populated"))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Overrides default to enable email as username field"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True"))

        return self.create_user(email, password, **extra_fields)

    def get_user_devices(self, user) -> QuerySet:
        """Return all devices created by user"""
        return (
            apps.get_model("devices", "Device")
            .objects.filter(user=user)
            .order_by("friendly_name")
        )

    def get_linked_devices(self, user) -> QuerySet:
        """Return list of device objects for user"""
        user_devices = self.get_user_devices(user=user).filter(
            Q(zigbeedevice__uuid__isnull=False)
            # | Q(apidevice_set__uuid__isnull=False) # not yet active
        )

        if not user_devices:
            return []

        return user_devices

    def get_controllable_devices(self, user) -> QuerySet:
        """Return list of device objects which can be controlled"""
        user_devices = self.get_linked_devices(user=user).filter(
            zigbeedevice__is_controllable=True
        )

        if not user_devices:
            return []

        return user_devices

    def total_linked_devices(self, user) -> int:
        """Return the number of linked devices for user object"""
        linked_devices = self.get_linked_devices(user=user)
        if not linked_devices:
            return 0

        return linked_devices.count()

    def get_user_notifications(self, user) -> QuerySet:
        return apps.get_model("notifications", "NotificationSetting").objects.filter(
            user=user
        )

    def get_active_notifications(self, user) -> QuerySet:
        """Return queryset of active notification mediums for specified user"""
        return self.get_user_notifications(user=user).filter(is_enabled=True)


class CustomUser(AbstractUser):
    """Customised user model"""

    username = None
    email = models.EmailField(_("email address"), unique=True)
    home_location = PointField(
        geography=True,
        default=Point(defines.DEFAULT_LONGTITUDE, defines.DEFAULT_LATITUDE),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        """Default redirect url for user object actions"""
        return reverse("users:account_profile")

    @property
    def get_user_devices(self) -> QuerySet:
        """Return queryset containing user's devices"""
        return CustomUser.objects.get_user_devices(user=self)

    @property
    def get_linked_devices(self) -> QuerySet:
        """Return queryset containing users linked devices"""
        return CustomUser.objects.get_linked_devices(user=self)

    @property
    def get_controllable_devices(self) -> QuerySet:
        """Return queryset containing users linked devices that are controllable devices"""
        return CustomUser.objects.get_controllable_devices(user=self)

    @property
    def total_linked_devices(self) -> int:
        """Return total number of linked devices for user"""
        total = 0
        try:
            total = self.get_linked_devices.count()
        except TypeError:
            # queryset is empty and count() does not exist
            pass

        return total
