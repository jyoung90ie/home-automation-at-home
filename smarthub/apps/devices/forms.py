"""Custom forms for handling creation of devices and device states"""
from django import forms

from . import models


class DeviceForm(forms.ModelForm):
    """Form for adding and updating a device. This is used to override default
    device location list which displays all locations (including other users)."""

    class Meta:
        model = models.Device
        fields = ["friendly_name", "device_identifier", "location", "protocol"]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        self.user = getattr(request, "user", None)

        super().__init__(*args, **kwargs)
        self.fields["location"] = forms.ModelChoiceField(
            queryset=models.DeviceLocation.objects.by_user(user=self.user)
        )


class DeviceStateForm(forms.ModelForm):
    """Form for creating device states - device field is polymorphic."""

    _device = forms.Field(label="Device", disabled=True)

    class Meta:
        model = models.DeviceState
        fields = ["_device", "name", "command", "command_value"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.device_uuid = kwargs.pop("device_uuid", None)
        self.device = models.Device.objects.filter(uuid=self.device_uuid).first()
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Attached custom field values and link to source device"""

        self.instance.content_object = (
            self.device.get_linked_device().first()
        )  # get the actual hardware device and store it (e.g. zigbee/api)

        super().save(commit=commit)
