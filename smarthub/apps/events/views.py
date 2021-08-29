"""Handles user requests to events app"""
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.generic.base import RedirectView
from django.apps import apps

from ..mixins import (
    AddUserToFormMixin,
    FormSuccessMessageMixin,
    LimitResultsToUserMixin,
    MakeRequestObjectAvailableInFormMixin,
    UserHasLinkedDevice,
)
from ..views import UUIDView
from . import forms, models
from .mixins import EventTriggerFormMixins, LimitResultsToEventOwner


class ListEvent(LimitResultsToUserMixin, ListView):
    """List all events that belong to requesting user"""

    model = models.Event
    paginate_by = 15
    context_object_name = "events"
    template_name = "events/event_list.html"
    ordering = ["created_at"]

    ordering = ["-is_enabled", "created_at"]

    def __init__(self) -> None:
        self.object = None
        super().__init__()


class DetailEvent(LimitResultsToUserMixin, UUIDView, DetailView):
    """Provides a detailed view of the user's event, including triggers"""

    model = models.Event
    context_object_name = "event"


class AddEvent(
    UserHasLinkedDevice,
    FormSuccessMessageMixin,
    AddUserToFormMixin,
    MakeRequestObjectAvailableInFormMixin,
    CreateView,
):
    """Enables user to create event and define the triggers that invoke it"""

    form_class = forms.EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:list")
    success_message = "The event has been created"


class UpdateEvent(
    FormSuccessMessageMixin, LimitResultsToEventOwner, UUIDView, UpdateView
):
    """Enables user to update their own event"""

    form_class = forms.EventForm
    template_name = "events/event_update_form.html"
    success_message = "The event has been updated"

    def get_queryset(self):
        """Populate with user's events only"""
        uuid = self.kwargs.get("uuid")
        return models.Event.objects.filter(uuid=uuid)


class DeleteEvent(LimitResultsToEventOwner, UUIDView, DeleteView):
    """Enables user to delete their own event"""

    model = models.Event
    success_url = reverse_lazy("events:list")
    template_name = "events/event_confirm_delete.html"

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def delete(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()

            messages.success(
                self.request,
                "The event has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except ProtectedError as ex:
            messages.error(
                request,
                "Could not delete the event - please try again.",
            )
            return HttpResponseRedirect(request.path)


class AddEventTrigger(
    FormSuccessMessageMixin,
    LimitResultsToEventOwner,
    EventTriggerFormMixins,
    UserHasLinkedDevice,
    CreateView,
):
    """Enables user to create event and define the triggers that invoke it"""

    form_class = forms.EventTriggerForm
    template_name = "events/event_trigger_form.html"
    success_message = "The event has been updated with the new trigger."


class UpdateEventTrigger(
    FormSuccessMessageMixin,
    LimitResultsToEventOwner,
    EventTriggerFormMixins,
    UUIDView,
    UpdateView,
):
    """Enables user to create event and define the triggers that invoke it"""

    form_class = forms.EventTriggerForm
    template_name = "events/event_trigger_update_form.html"
    slug_url_kwarg = "tuuid"
    success_message = "The event trigger has been updated."

    def get_queryset(self):
        return models.EventTrigger.objects.filter(uuid=self.kwargs["tuuid"])

    def get_form(self, form_class=None):
        """Device is already selected - get device specific metadata"""
        form = super().get_form(form_class=form_class)

        device = getattr(self.get_object(), "device", "")

        zigbee_device = apps.get_model("zigbee", "ZigbeeDevice")
        form.fields["_metadata_field"].choices = [
            (field, field)
            for field in zigbee_device.objects.get_metadata_fields(device)
        ]

        return form

    def get_initial(self):
        """Populate update form with stored data"""
        initial = super().get_initial()
        obj = self.get_object()

        device = getattr(obj, "device", "")
        field = getattr(obj, "metadata_field", "")

        initial["_device"] = (device.uuid, device.friendly_name) if device else ""
        initial["_metadata_field"] = field if field else ""

        return initial


class DeleteEventTrigger(LimitResultsToEventOwner, UUIDView, DeleteView):
    """Enables user to delete an event trigger"""

    model = models.EventTrigger
    template_name = "events/event_trigger_confirm_delete.html"
    slug_url_kwarg = "tuuid"

    def get_success_url(self):
        return reverse_lazy("events:event:detail", kwargs={"uuid": self.kwargs["uuid"]})

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def delete(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()

            messages.success(
                request,
                "The event trigger has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except Exception:
            messages.error(
                request,
                "There was a problem deleting the event trigger - please try again.",
            )
            return HttpResponseRedirect(request.path)


class EventDetailRedirectView(RedirectView):
    """Redirects URL to proper update path - for breadcrumb"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse("events:event:detail", kwargs={"uuid": kwargs.pop("uuid")})


class EventTriggerRedirectView(RedirectView):
    """Redirects URL to proper update path - for breadcrumb"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "events:event:triggers:trigger:update",
            kwargs={"uuid": kwargs.pop("uuid"), "tuuid": kwargs.pop("tuuid")},
        )
