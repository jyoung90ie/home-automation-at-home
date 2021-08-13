from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    DetailView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from . import models, forms, mixins
from ..mixins import MakeRequestObjectAvailableInFormMixin, AddUserToFormMixin
from ..views import UUIDView
from django.apps import apps
from django.core.paginator import Paginator

DeviceModel = models.Device


class AddDeviceLocation(LoginRequiredMixin, AddUserToFormMixin, CreateView):
    model = models.DeviceLocation
    fields = [
        "location",
    ]


class UpdateDeviceLocation(UUIDView, mixins.LimitResultsToUserMixin, UpdateView):
    model = models.DeviceLocation
    fields = ["location"]
    template_name_suffix = "_update"


class DeleteDeviceLocation(UUIDView, mixins.LimitResultsToUserMixin, DeleteView):
    model = models.DeviceLocation
    success_url = reverse_lazy("devices:locations:list")


class ListDeviceLocations(mixins.LimitResultsToUserMixin, ListView):
    model = models.DeviceLocation
    paginate_by = 10
    context_object_name = "device_locations"
    template_name = "devicelocation_list.html"


class AddDevice(
    LoginRequiredMixin,
    MakeRequestObjectAvailableInFormMixin,
    AddUserToFormMixin,
    CreateView,
):
    form_class = forms.AddDeviceForm
    template_name = "devices/device_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["locations"] = models.DeviceLocation.objects.filter(
            user=self.request.user
        )
        return context


class UpdateDevice(UUIDView, mixins.LimitResultsToUserMixin, UpdateView):
    model = DeviceModel
    fields = ["friendly_name", "device_identifier", "location", "protocol"]
    template_name_suffix = "_update_form"


class DeleteDevice(UUIDView, mixins.LimitResultsToUserMixin, DeleteView):
    model = DeviceModel
    success_url = reverse_lazy("devices:list")


class ListDevices(UUIDView, mixins.LimitResultsToUserMixin, ListView):
    model = DeviceModel
    paginate_by = 10
    context_object_name = "devices"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["protocols"] = models.Device.DeviceProtocol.__members__
        return context


class DetailDevice(UUIDView, mixins.LimitResultsToUserMixin, DetailView):
    model = DeviceModel
    context_object_name = "device"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uuid"] = self.kwargs.get("uuid")
        return context


class LogsForDevice(UUIDView, mixins.LimitResultsToUserMixin, ListView):
    paginate_by = 5
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
        queryset = self.device.get_zigbee_logs()
        return queryset
