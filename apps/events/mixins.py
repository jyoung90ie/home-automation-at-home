"""Custom class overrides that provide additional functionality"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.urls.base import reverse

from . import models


class FormsRelatedToUserEventsMixin:
    """Form overrides to enable fields populated by javascript to be used"""

    controllabe_devices_only = False

    def get_form_kwargs(self):
        """Passes additional objects to form class to enable custom validation"""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["event_uuid"] = self.kwargs["uuid"]
        return kwargs

    def get_form(self, form_class=None):
        """Override the default device queryset to constrain options to only those
        that belong to the user and have been linked to a hardware device (and thus
        have metadata)"""
        form = super().get_form(form_class)

        if getattr(self, "controllable_devices_only", False):
            devices = self.request.user.get_controllable_devices
        else:
            devices = self.request.user.get_linked_devices

        if not getattr(self, "is_update_form", False):
            form.fields["_device"].choices = [
                (device.uuid, device.friendly_name.title()) for device in devices
            ]

        return form

    def get_success_url(self) -> str:
        return reverse(
            "events:event:detail", kwargs={"uuid": self.get_form_kwargs()["event_uuid"]}
        )


class LimitResultsToEventOwner(LoginRequiredMixin):
    """This differs to LimitResultsToUserMixin in that it traverses a foreign key to filter by
    user as the EventTrigger object does not have direct access to the user"""

    def dispatch(self, request, *args, **kwargs):

        obj = get_object_or_404(models.Event, user=request.user, uuid=kwargs["uuid"])
        if not obj:
            return Http404("Could not find the Event")
        return super().dispatch(request, *args, **kwargs)
