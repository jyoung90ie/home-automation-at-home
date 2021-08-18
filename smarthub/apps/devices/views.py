from django.contrib import messages as flash_message
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.http.response import HttpResponseRedirect
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    DetailView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView

from csv_export.views import CSVExportView

from . import models, forms, mixins
from ..mixins import MakeRequestObjectAvailableInFormMixin, AddUserToFormMixin
from ..views import UUIDView


class AddDeviceLocation(LoginRequiredMixin, CreateView):
    model = models.DeviceLocation
    fields = [
        "location",
    ]

    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            self.object = form.save()

            flash_message.success(
                self.request,
                "The new device location has been added - you have been redirected to it.",
            )
            return super().form_valid(form)
        except IntegrityError as ex:
            flash_message.error(
                self.request,
                "You already have a device location with this name - please change the location name and try again",
            )
            return self.form_invalid(form)


class DetailDeviceLocation(UUIDView, DetailView):
    model = models.DeviceLocation
    context_object_name = "location"

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


class UpdateDeviceLocation(UUIDView, mixins.LimitResultsToUserMixin, UpdateView):
    model = models.DeviceLocation
    fields = ["location"]
    template_name_suffix = "_update"

    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            self.object = form.save()

            flash_message.success(
                self.request,
                "The device location has been updated.",
            )
            return super().form_valid(form)
        except IntegrityError as ex:
            flash_message.error(
                self.request,
                "You already have a device location with this name - please change the location name and try again",
            )
            return self.form_invalid(form)


class DeleteDeviceLocation(UUIDView, mixins.LimitResultsToUserMixin, DeleteView):
    model = models.DeviceLocation
    success_url = reverse_lazy("devices:locations:list")

    def delete(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()

            flash_message.success(
                self.request,
                "The device location has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except ProtectedError as ex:
            error_message = "Cannot delete item because it is being used by one or more of your devices - please update this device and try again"
            devices = ",".join(
                [device.friendly_name for device in ex.protected_objects]
            )

            flash_message.warning(
                request,
                f"{error_message}  (Devices: {devices})",
            )
            return HttpResponseRedirect(request.path)


class ListDeviceLocations(mixins.LimitResultsToUserMixin, ListView):
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
    form_class = forms.DeviceForm
    template_name = "devices/device_form.html"

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

            flash_message.success(
                self.request,
                "The new device has been created - you have been redirected to it.",
            )
            return super().form_valid(form)
        except IntegrityError as ex:
            flash_message.error(
                self.request,
                "You already have a device with this device identifier - please change it and try again",
            )
            return self.form_invalid(form)


class UpdateDevice(
    UUIDView,
    MakeRequestObjectAvailableInFormMixin,
    mixins.LimitResultsToUserMixin,
    UpdateView,
):
    form_class = forms.DeviceForm
    template_name_suffix = "_update_form"

    def get_queryset(self):
        return models.Device.objects.filter(uuid=self.kwargs["uuid"])

    def form_valid(self, form):
        try:
            self.object = form.save()

            flash_message.success(
                self.request,
                "The device has been updated.",
            )
            return super().form_valid(form)
        except IntegrityError as ex:
            flash_message.error(
                self.request,
                "You already have a device with this device identifier - please change it and try again",
            )
            return self.form_invalid(form)


class DeleteDevice(UUIDView, mixins.LimitResultsToUserMixin, DeleteView):
    model = models.Device
    success_url = reverse_lazy("devices:list")

    def delete(self, request, *args, **kwargs):

        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()

            flash_message.success(
                request,
                "The device has been deleted.",
            )

            return HttpResponseRedirect(success_url)
        except Exception as ex:
            flash_message.error(
                request,
                "There was a problem deleting this device - please try again.",
            )
            return HttpResponseRedirect(request.path)

    def form_valid(self, form):
        flash_message.success(
            self.request,
            "The device has been deleted.",
        )
        return super().form_valid(form)


class ListDevices(UUIDView, mixins.LimitResultsToUserMixin, ListView):
    model = models.Device
    paginate_by = 15
    context_object_name = "devices"
    ordering = ["created_at"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["protocols"] = models.DeviceProtocol.__members__
        return context


class DetailDevice(UUIDView, mixins.PermitDeviceOwnerOnly, DetailView):
    model = models.Device
    context_object_name = "device"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uuid"] = self.kwargs.get("uuid")
        return context


class LogsForDevice(UUIDView, mixins.PermitDeviceOwnerOnly, ListView):
    paginate_by = 15
    context_object_name = "logs"
    template_name = "devices/device_logs.html"
    ordering = ["-created_at"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["device"] = self.device
        return context

    def get_queryset(self):
        uuid = self.kwargs.pop("uuid")
        self.device = models.Device.objects.get(uuid=uuid)
        queryset = self.device.get_zigbee_messages()
        return queryset


class ExportCSVDeviceLogs(CSVExportView, LogsForDevice):
    """Exports logs for specified device"""

    exclude = ("id", "uuid", "zigbee_device", "updated_at", "topic")
