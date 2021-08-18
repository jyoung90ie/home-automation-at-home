"""Handles user requests to events app"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from . import models, forms
from ..views import UUIDView
from ..mixins import (
    LimitResultsToUserMixin,
    AddUserToFormMixin,
    MakeRequestObjectAvailableInFormMixin,
)


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
    LoginRequiredMixin,
    AddUserToFormMixin,
    MakeRequestObjectAvailableInFormMixin,
    CreateView,
):
    """Enables user to create event and define the triggers that invoke it"""

    form_class = forms.EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:list")

    def form_valid(self, form):
        """Overrides default to add user message on success"""
        kwargs = self.get_form_kwargs()
        request = kwargs["request"]

        messages.success(self.request, "New event added")
        return super().form_valid(form)


class UpdateEvent(LimitResultsToUserMixin, UUIDView, UpdateView):
    """Enables user to update their own event"""

    form_class = forms.EventForm
    template_name = "events/event_update_form.html"

    def get_queryset(self):
        """Populate with user's events only"""
        uuid = self.kwargs.get("uuid")
        return models.Event.objects.filter(uuid=uuid)

    def form_valid(self, form):
        messages.success(self.request, "Event has been updated")
        return super().form_valid(form)


class DeleteEvent(LimitResultsToUserMixin, UUIDView, DeleteView):
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
            error_message = (
                "Could not delete event as it is linked to another device(s) - "
            )
            devices = ",".join(
                [device.friendly_name for device in ex.protected_objects]
            )

            messages.warning(
                request,
                f"{error_message}  (Devices: {devices})",
            )
            return HttpResponseRedirect(request.path)
