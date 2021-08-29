"""Handles user requests to devices app"""

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.http.response import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)
from django.views.generic.detail import BaseDetailView

from csv_export.views import CSVExportView

from ..mixins import (
    AddUserToFormMixin,
    FormSuccessMessageMixin,
    LimitResultsToUserMixin,
    MakeRequestObjectAvailableInFormMixin,
)

from .mixins import PermitDeviceOwnerOnly, DeviceStateFormMixin

from ..views import UUIDView
from . import forms, mixins, models


class AddDeviceLocation(LoginRequiredMixin, CreateView):
    """Handles creation of device locations"""

    model = models.DeviceLocation
    fields = [
        "location",
    ]

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            self.object = form.save()

            messages.success(
                self.request,
                "The new device location has been added - you have been redirected to it.",
            )
            return super().form_valid(form)
        except IntegrityError:

            messages.error(
                self.request,
                "You already have a device location with this name - please change the location"
                " name and try again",
            )
            return self.form_invalid(form)


class DetailDeviceLocation(LimitResultsToUserMixin, UUIDView, DetailView):
    """Handles serving of specific device information"""

    model = models.DeviceLocation
    context_object_name = "location"
    ordering = "created_at"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uuid"] = self.kwargs.get("uuid")
        context[
            "total_zigbee"
        ] = models.DeviceLocation.objects.total_zigbee_by_location(
            location=self.get_object()
        )
        context["total_api"] = models.DeviceLocation.objects.total_api_by_location(
            location=self.get_object()
        )

        return context


class UpdateDeviceLocation(UUIDView, LimitResultsToUserMixin, UpdateView):
    """Handles updating of a specific device"""

    model = models.DeviceLocation
    fields = ["location"]
    template_name_suffix = "_update"

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            self.object = form.save()

            messages.success(
                self.request,
                "The device location has been updated.",
            )
            return super().form_valid(form)
        except IntegrityError:
            messages.error(
                self.request,
                "You already have a device location with this name - please change the location "
                "name and try again",
            )
            return self.form_invalid(form)


class DeleteDeviceLocation(UUIDView, LimitResultsToUserMixin, DeleteView):
    """Enables user to delete device locations they have created"""

    model = models.DeviceLocation
    success_url = reverse_lazy("devices:locations:list")

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
                "The device location has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except ProtectedError as ex:
            error_message = (
                "Cannot delete item because it is being used by one or more of your "
                "devices - please update this device and try again"
            )
            devices = ",".join(
                [device.friendly_name for device in ex.protected_objects]
            )

            messages.warning(
                request,
                f"{error_message}  (Devices: {devices})",
            )
            return HttpResponseRedirect(request.path)


class DeviceMetadata(UUIDView, BaseDetailView):
    """Return distinct list of device's metadata - for user in event trigger form with AJAX"""

    http_method_names = [
        "get",
    ]

    def __init__(self) -> None:
        self.request = None
        super().__init__()

    def get_object(self, queryset=None):
        """Prevent user from accessing devices that aren't theirs"""
        return get_object_or_404(
            models.Device, uuid=self.kwargs["uuid"], user=self.request.user
        )

    def get(self, request, *args, **kwargs):
        """Create JSON response with list of metadata fields from logs"""
        self.request = request
        device = self.get_object()

        try:
            zigbee_device = apps.get_model("zigbee", "ZigbeeDevice")
            metadata_fields = zigbee_device.objects.get_metadata_fields(device)
            json_data = list(metadata_fields)
        except Exception as ex:
            metadata_on_error = ("", "-----")
            json_data = list(metadata_on_error)

        return JsonResponse({"data": json_data}, safe=False)


class ListDeviceLocations(LimitResultsToUserMixin, ListView):
    """Handles listing of device locations created by the user"""

    model = models.DeviceLocation
    paginate_by = 15
    context_object_name = "device_locations"
    template_name = "devicelocation_list.html"
    ordering = ["created_at"]


class UpdateDeviceLocationRedirectView(RedirectView):
    """Redirects URL to proper update path - for breadcrumb"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy(
            "devices:locations:update", kwargs={"uuid": kwargs.pop("uuid")}
        )


class AddDevice(
    LoginRequiredMixin,
    MakeRequestObjectAvailableInFormMixin,
    AddUserToFormMixin,
    CreateView,
):
    """Handles creation of a new device for the user"""

    form_class = forms.DeviceForm
    template_name = "devices/device_form.html"

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # used to check user has at least one device location to attach their device to
        context["locations"] = models.DeviceLocation.objects.filter(
            user=self.request.user
        )
        return context

    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            self.object = form.save()

            messages.success(
                self.request,
                "The new device has been created - you have been redirected to it.",
            )
            return super().form_valid(form)
        except IntegrityError as ex:

            cause = (
                "friendly name" if "friendly_name" in str(ex) else "device identifier"
            )
            messages.error(
                self.request,
                f"You already have a device with this {cause} - please change it and try again",
            )
            return self.form_invalid(form)


class UpdateDevice(
    UUIDView,
    MakeRequestObjectAvailableInFormMixin,
    LimitResultsToUserMixin,
    UpdateView,
):
    """Handles updating of an existing device for the specified user"""

    form_class = forms.DeviceForm
    template_name_suffix = "_update_form"

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def get_queryset(self):
        return models.Device.objects.filter(uuid=self.kwargs["uuid"])

    def form_valid(self, form):
        try:
            self.object = form.save()

            messages.success(
                self.request,
                "The device has been updated.",
            )
            return super().form_valid(form)
        except IntegrityError:
            messages.error(
                self.request,
                "You already have a device with this device identifier - please change it and "
                "try again",
            )
            return self.form_invalid(form)


class DeleteDevice(UUIDView, LimitResultsToUserMixin, DeleteView):
    """Enables user to delete any of their own devices"""

    model = models.Device
    success_url = reverse_lazy("devices:list")

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
                "The device has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except Exception:
            messages.error(
                request,
                "There was a problem deleting this device - please try again.",
            )
            return HttpResponseRedirect(request.path)


class ListDevices(UUIDView, LimitResultsToUserMixin, ListView):
    """Enables user to list all of their devices"""

    model = models.Device
    paginate_by = 15
    context_object_name = "devices"
    ordering = ["created_at"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["protocols"] = models.DeviceProtocol.__members__
        return context


class DetailDevice(UUIDView, mixins.PermitDeviceOwnerOnly, DetailView):
    """Enables user to view detailed information on their own device"""

    model = models.Device
    context_object_name = "device"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uuid"] = self.kwargs.get("uuid")
        return context


class LogsForDevice(UUIDView, mixins.PermitDeviceOwnerOnly, ListView):
    """Enables user to view hardware device logs - if their device has been linked to a
    hadware device"""

    paginate_by = 15
    context_object_name = "logs"
    template_name = "devices/device_logs.html"
    ordering = ["-created_at"]

    def __init__(self) -> None:
        self.device = None
        super().__init__()

    def get_context_data(self, **kwargs):
        """Passes through device object to the template"""
        context = super().get_context_data(**kwargs)
        context["device"] = self.device
        return context

    def get_queryset(self):
        """Queryset used to populate form"""
        uuid = self.kwargs.pop("uuid")
        self.device = models.Device.objects.get(uuid=uuid)

        queryset = self.device.get_zigbee_messages()
        if not queryset:
            raise Http404("Could not find device logs")

        return queryset


class ExportCSVDeviceLogs(CSVExportView, LogsForDevice):
    """Exports logs for specified device"""

    exclude = ("id", "uuid", "zigbee_device", "updated_at", "topic")


class DeviceRedirectView(RedirectView):
    """Redirects URL to proper update path - for breadcrumb"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse("devices:device:detail", kwargs={"uuid": kwargs.pop("uuid")})


class AddDeviceState(
    FormSuccessMessageMixin,
    DeviceStateFormMixin,
    PermitDeviceOwnerOnly,
    UUIDView,
    CreateView,
):
    """Handles create form - including injection of user devices"""

    form_class = forms.DeviceStateForm
    template_name = "devices/device_state_form.html"
    success_message = "New state added for this device"

    def get_initial(self):
        """Populate update form with stored data"""
        initial = super().get_initial()
        device = self.get_object()
        initial["_device"] = device.friendly_name

        return initial

    def get_queryset(self):
        """Queryset used to populate form - using device to pull device info from URL"""
        return models.Device.objects.filter(uuid=self.kwargs["uuid"])


class UpdateDeviceState(
    FormSuccessMessageMixin,
    DeviceStateFormMixin,
    PermitDeviceOwnerOnly,
    UUIDView,
    UpdateView,
):
    """Handles data and rendering for update form"""

    form_class = forms.DeviceStateForm
    template_name = "devices/device_state_update_form.html"
    slug_url_kwarg = "suuid"
    success_message = "State values have been updated"

    def get_initial(self):
        """Populate update form with stored data"""
        initial = super().get_initial()
        device_state = self.get_object()
        initial["_device"] = device_state.friendly_name

        return initial

    def get_queryset(self):
        """Queryset used to populate form"""
        return models.DeviceState.objects.filter(uuid=self.kwargs["suuid"])


class DeleteDeviceState(UUIDView, PermitDeviceOwnerOnly, DeleteView):
    """Enables user to delete any of their own device states"""

    model = models.DeviceState
    slug_url_kwarg = "suuid"
    template_name = "devices/device_state_confirm_delete.html"

    def __init__(self) -> None:
        self.object = None
        super().__init__()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["device_uuid"] = self.kwargs.get("uuid")
        return context

    def get_success_url(self) -> str:
        return reverse_lazy(
            "devices:device:detail", kwargs={"uuid": self.kwargs.get("uuid")}
        )

    def delete(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()

            messages.success(
                request,
                "The device state has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except Exception:
            messages.error(
                request,
                "There was a problem deleting this device state - please try again.",
            )
            return HttpResponseRedirect(request.path)


class DeviceStatesJson(UUIDView, BaseDetailView):
    """Return list of device states - for user in event response form with AJAX"""

    http_method_names = [
        "get",
    ]

    def __init__(self) -> None:
        self.request = None
        super().__init__()

    def get_object(self, queryset=None):
        """Prevent user from accessing devices that aren't theirs"""
        return get_object_or_404(
            models.Device, uuid=self.kwargs["uuid"], user=self.request.user
        )

    def get(self, request, *args, **kwargs):
        """Create JSON response with list of metadata fields from logs"""
        self.request = request
        device = self.get_object()

        default_return = (
            "",
            "Device does not have any states",
        )

        try:
            hardware_device = device.get_linked_device().first()
            device_obj = type(hardware_device)

            device_states = device_obj.objects.get_device_states(device=device)

            device_states = [
                (
                    state["device_states__uuid"],
                    state["device_states__name"].capitalize(),
                )
                for state in device_states
            ]
            # json removes tuple - needs to be handled in JS to ensure correct data rendered
            json_data = device_states
        except Exception as ex:
            metadata_on_error = default_return
            json_data = list(metadata_on_error)

        return JsonResponse({"data": json_data}, safe=False)
