from . import models
from django import forms


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
