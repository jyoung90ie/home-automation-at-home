"""Custom forms for handling creation of events with event trigger objects"""

from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Fieldset, Layout, Row, Submit

from ..zigbee.models import METADATA_TYPE_FIELD, ZigbeeDevice
from . import models


class EventForm(forms.ModelForm):
    """Create events and event triggers"""

    class Meta:
        model = models.Event
        fields = [
            "description",
            "is_enabled",
            "send_notification",
            "notification_topic",
            "notification_message",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        self.user = getattr(request, "user", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "create_notification"
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-5"
        self.helper.field_class = "col-md-7"
        self.helper.form_method = "post"
        self.helper.form_action = "events:add"

        self.helper.layout = Layout(
            Row(
                Field("description"),
                Field(
                    "is_enabled",
                    title="Enable event?",
                ),
                Field(
                    "send_notification",
                    title="Send notifications when event is triggered?",
                ),
            ),
            Row(
                Column("notification_topic"),
                Column("notification_message"),
            ),
            Fieldset("Event Trigger(s)", Row(Column())),
        )

        self.helper.add_input(
            Submit("submit", "Create Event", css_class="btn btn-primary")
        )


class CustomChoiceField(forms.ChoiceField):
    """Overrides validation method to prevent validation against default list of choices. This
    enables custom validation to be performed in form.clean() method as the data is accessible
    via cleaned_data dict.

    IMPORTANT - default validation is removed using this class"""

    def validate(self, value) -> None:
        """Removes validation against initial choices list"""
        if value in self.empty_values and self.required:
            raise ValidationError(
                self.error_messages["required"], code="required")
        return True


class EventTriggerForm(forms.ModelForm):
    """Custom form for capturing event trigger data"""

    _device = CustomChoiceField(
        label="Device", required=True, choices=[("", "-----")])

    _metadata_field = CustomChoiceField(
        label="Device data field", choices=[("", "-----")]
    )

    class Meta:
        model = models.EventTrigger
        fields = [
            "_device",
            "is_enabled",
            "_metadata_field",
            "metadata_trigger_value",
            "trigger_type",
            "is_enabled",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.event_uuid = kwargs.pop("event_uuid", None)
        self.device = None
        super().__init__(*args, **kwargs)

    def clean(self):
        clean = super().clean()
        error_message = (
            "Select a valid choice. The value you selected is not one of the"
            " available choices."
        )
        # form field names
        device_field_name = "_device"
        metadata_field_name = "_metadata_field"

        # form values
        form_device = clean[device_field_name]
        form_metadata = clean[metadata_field_name]

        # device validation
        device = self.request.user.get_linked_devices.filter(uuid=form_device)

        if form_device and not device.exists():
            self.add_error(
                device_field_name,
                error_message,
            )
        else:
            self.device = device.get()

        # metadata validation
        valid_metadata = ZigbeeDevice.objects.get_metadata_fields(
            device=self.device)

        if (
            form_metadata
            and not valid_metadata.filter(
                **{METADATA_TYPE_FIELD: form_metadata}
            ).exists()
        ):
            self.add_error(
                metadata_field_name,
                error_message,
            )
        return clean

    def save(self, commit=True):
        """Attached custom field values and link to source event"""
        self.instance.event = models.Event.objects.get(uuid=self.event_uuid)
        self.instance.device = self.device
        self.instance.metadata_field = self.cleaned_data["_metadata_field"]

        return super().save(commit=commit)
