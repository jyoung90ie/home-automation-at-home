from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls.base import reverse

from . import models


class PermitDeviceOwnerOnly(LoginRequiredMixin):
    """Override queryset to only show results for current user. This prevents user from
    accessing objects they do not own."""

    def dispatch(self, request, *args, **kwargs):
        uuid = kwargs.pop("uuid")
        device = get_object_or_404(models.Device, uuid=uuid, user=self.request.user)
        if not device:
            return device

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
