"""Handles user requests to events app"""
from django.apps import apps
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.views.generic.base import RedirectView

from ..mixins import (AddUserToFormMixin, FormSuccessMessageMixin,
                      LimitResultsToUserMixin,
                      MakeRequestObjectAvailableInFormMixin,
                      UserHasLinkedDevice)
from ..views import UUIDView
from . import forms, models
from .mixins import FormsRelatedToUserEventsMixin, LimitResultsToEventOwner


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("context", context["event"], dir(context["event"]))
        print(
            "response set",
            context["event"].eventresponse_set.first().device_state,
            dir(context["event"].eventresponse_set.first().device_state),
        )
        return context


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
    FormsRelatedToUserEventsMixin,
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
    FormsRelatedToUserEventsMixin,
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


class AddEventResponse(
    FormSuccessMessageMixin,
    LimitResultsToEventOwner,
    FormsRelatedToUserEventsMixin,
    UserHasLinkedDevice,
    CreateView,
):
    """Enables user to configure responses to an event trigger"""

    form_class = forms.EventResponseForm
    template_name = "events/event_response_form.html"
    success_message = "A new Response has been added to this Event."


class EventResponseRedirectView(RedirectView):
    """Redirects URL to proper update path - for breadcrumb"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "events:event:triggers:trigger:update",
            kwargs={"uuid": kwargs.pop("uuid"), "ruuid": kwargs.pop("ruuid")},
        )


class UpdateEventResponse(
    FormSuccessMessageMixin,
    LimitResultsToEventOwner,
    FormsRelatedToUserEventsMixin,
    UUIDView,
    UpdateView,
):
    """Enables a user to change is_enabled & device state, but not device"""

    form_class = forms.EventResponseUpdateForm
    template_name = "events/event_response_update_form.html"
    slug_url_kwarg = "ruuid"
    success_message = "The event response has been updated."

    def get_queryset(self):
        return models.EventResponse.objects.filter(uuid=self.kwargs["ruuid"])

    def get_form_kwargs(self):
        """Passes additional objects to form class to enable custom validation"""
        kwargs = super().get_form_kwargs()
        kwargs["device"] = self.get_object().device_state.user_device_obj
        return kwargs

    def get_form(self, form_class=None):
        """Device is already selected - get device specific metadata"""
        form = super().get_form(form_class=form_class)
        event_response = self.get_object()

        user_device = event_response.device_state.user_device_obj
        hardware_device_obj = type(event_response.device_state.hardware_device_obj)

        form.fields["_state"].choices = [
            (
                state["device_states__uuid"],
                state["device_states__name"].capitalize(),
            )
            for state in hardware_device_obj.objects.get_device_states(
                device=user_device
            )
        ]

        return form

    def get_initial(self):
        """Populate update form with stored data"""
        initial = super().get_initial()
        event_response = self.get_object()
        state = event_response.device_state

        user_device = event_response.device_state.user_device_obj

        initial["_device"] = user_device.friendly_name if user_device else ""
        initial["_state"] = state.uuid if state else ""

        return initial


class DeleteEventResponse(LimitResultsToEventOwner, UUIDView, DeleteView):
    """Enables user to delete an event trigger"""

    model = models.EventResponse
    template_name = "events/event_response_confirm_delete.html"
    slug_url_kwarg = "ruuid"

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_uuid"] = self.kwargs.get("uuid")
        return context

    def get_success_url(self):
        return reverse_lazy("events:event:detail", kwargs={"uuid": self.kwargs["uuid"]})

    def delete(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()

            messages.success(
                request,
                "The event response has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except Exception:
            messages.error(
                request,
                "There was a problem deleting the event response - please try again.",
            )
            return HttpResponseRedirect(request.path)
