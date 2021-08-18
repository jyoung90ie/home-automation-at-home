from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

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
