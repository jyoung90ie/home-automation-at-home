from django.contrib.auth.mixins import AccessMixin
from django.http.response import Http404
from django.urls.base import reverse

from .models import Device


class PermitObjectOwnerOnly(AccessMixin):
    """Anonymous users will be redirected to login and already authenticated users that are not
    the object (e.g. device) owner will be shown a 403 message."""

    def dispatch(self, request, *args, **kwargs):
        uuid = kwargs.pop("uuid")

        if not request.user.is_authenticated:
            return self.handle_no_permission()

        user = getattr(request, "user", None)
        obj = type(self.get_object())
        qs = obj.objects.filter(uuid=uuid, user=user)

        if not qs:
            return self.handle_no_permission()

        # for restricting devicestate views
        if getattr(self, "controllable_only", False):
            device = qs.first()
            if not device.is_controllable():
                raise Http404("Device does not support states")

        return super().dispatch(request, *args, **kwargs)


class DeviceStateFormMixin:
    """Form overrides to enable fields populated by javascript to be used"""

    def get_form_kwargs(self):
        """Passes additional objects to form class to enable custom validation"""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["device_uuid"] = self.kwargs["uuid"]
        return kwargs

    def get_success_url(self) -> str:
        """Redirect URL on successful submission of form"""
        return reverse(
            "devices:device:detail",
            kwargs={"uuid": self.get_form_kwargs()["device_uuid"]},
        )


class PermitDeviceOwnerOnly(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        uuid = kwargs.pop("uuid")

        if not request.user.is_authenticated:
            return self.handle_no_permission()

        user = getattr(request, "user", None)
        qs = Device.objects.filter(uuid=uuid, user=user)

        if not qs:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
