"""Custom forms for handling creation of devices and device states"""
from django import forms

from . import models
from ..forms import CustomChoiceField


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

    _device = CustomChoiceField(label="Device", required=True, choices=[("", "-----")])

    class Meta:
        model = models.DeviceState
        fields = ["_device", "name", "command", "command_value"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.device_uuid = kwargs.pop("device_uuid", None)
        self.device = None
        self.device_object_id = None
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate manual fields - raise form errors if unexpected values found"""
        clean = super().clean()
        error_message = (
            "Select a valid choice. The value you selected is not one of the"
            " available choices."
        )
        # form field names
        device_field_name = "_device"

        # form values
        form_device = clean[device_field_name]

        # device validation
        device = self.request.user.get_linked_devices.filter(uuid=form_device)

        if form_device and not device.exists():
            self.add_error(
                device_field_name,
                error_message,
            )
        else:
            self.device = device.get()

        return clean

    def save(self, commit=True):
        """Attached custom field values and link to source device"""
        self.instance.content_object = (
            self.device.get_linked_device()
        )  # get the actual hardware device and store it (e.g. zigbee/api)

        super().save(commit=commit)
