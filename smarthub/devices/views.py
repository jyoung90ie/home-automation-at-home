from django.shortcuts import render
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
from smarthub.mixins import MakeRequestObjectAvailableInFormMixin, AddUserToFormMixin
from smarthub.views import UUIDView


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
    model = models.Device
    fields = ["friendly_name", "device_identifier", "location", "protocol"]
    template_name_suffix = "_update_form"


class DeleteDevice(UUIDView, mixins.LimitResultsToUserMixin, DeleteView):
    model = models.Device
    success_url = reverse_lazy("devices:list")


class ListDevices(UUIDView, mixins.LimitResultsToUserMixin, ListView):
    model = models.Device
    paginate_by = 10
    context_object_name = "devices"


class DetailDevice(UUIDView, mixins.LimitResultsToUserMixin, DetailView):
    model = models.Device
    context_object_name = "device"
