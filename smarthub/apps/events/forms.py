"""Custom forms for handling creation of events with event trigger objects"""

import logging

from django import forms
from django.apps import apps

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Fieldset, Layout, Row, Submit

from ..events.defines import NON_NUMERIC_TRIGGER_TYPES, NUMERIC_TRIGGER_TYPES
from ..forms import CustomChoiceField
from ..zigbee.models import METADATA_TYPE_FIELD, ZigbeeDevice
from . import models

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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


class EventTriggerForm(forms.ModelForm):
    """Custom form for capturing event trigger data"""

    _device = CustomChoiceField(label="Device", required=True, choices=[("", "-----")])

    _metadata_field = CustomChoiceField(
        label="Device data field", choices=[("", "-----")]
    )

    class Meta:
        model = models.EventTrigger
        fields = [
            "_device",
            "is_enabled",
            "_metadata_field",
            "trigger_type",
            "metadata_trigger_value",
            "is_enabled",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.event_uuid = kwargs.pop("event_uuid", None)
        self.device = None
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate manual fields - raise form errors if unexpected values found"""
        logger.info("Start EventTriggerForm clean()")
        clean = super().clean()
        error_message = (
            "Select a valid choice. The value you selected is not one of the"
            " available choices."
        )
        # form field names
        device_field_name = "_device"
        metadata_field_name = "_metadata_field"
        trigger_type_field_name = "trigger_type"
        trigger_value_field_name = "metadata_trigger_value"

        # form values
        form_device = clean[device_field_name]
        form_metadata = clean[metadata_field_name]
        form_trigger_type = clean[trigger_type_field_name]
        form_trigger_value = clean[trigger_value_field_name]

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
        valid_metadata = ZigbeeDevice.objects.get_metadata_fields(device=self.device)

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

        # number must be numeric if numeric trigger type selected
        if form_trigger_type in NUMERIC_TRIGGER_TYPES:
            try:
                int(form_trigger_value)
            except ValueError:
                self.add_error(
                    trigger_value_field_name,
                    "Value must be numeric with the specified trigger type",
                )

                non_numeric_options = ", ".join(
                    [trigger.upper() for trigger in NON_NUMERIC_TRIGGER_TYPES]
                )

                self.add_error(
                    trigger_type_field_name,
                    f"If you wish to use a non-numeric trigger value, you can select one"
                    " of the following: {non_numeric_options}",
                )

        logger.info("Finish EventTriggerForm clean()")
        return clean

    def save(self, commit=True):
        """Attached custom field values and link to source event"""
        logger.info("Start EventTriggerForm save()")
        self.instance.event = models.Event.objects.get(uuid=self.event_uuid)
        self.instance.device = self.device
        self.instance.metadata_field = self.cleaned_data["_metadata_field"]

        super().save(commit=commit)
        logger.info("Finish EventTriggerForm save()")


class EventResponseForm(forms.ModelForm):
    """Custom form for creating and updating EventResponse objects"""

    _device = CustomChoiceField(label="Device", required=True, choices=[("", "-----")])
    _state = CustomChoiceField(
        label="Device state", required=True, choices=[("", "-----")]
    )

    class Meta:
        model = models.EventResponse
        fields = [
            "_device",
            "_state",
            "is_enabled",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.event_uuid = kwargs.pop("event_uuid", None)
        self.device = kwargs.pop("device", None)
        self.state_uuid = None
        self.is_update_form = False

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
        state_field = "_state"
        try:
            # form values
            form_device = clean[device_field_name]
            form_state = clean[state_field]

            # device validation
            if not self.is_update_form:
                device = self.request.user.get_controllable_devices.filter(
                    uuid=form_device
                )

                if form_device and not device.exists():
                    self.add_error(
                        device_field_name,
                        error_message,
                    )
                device = device.get()
            else:
                device = self.device

            hardware_device = device.get_linked_device().first()
            hardware_device_obj = type(hardware_device)

            device_state = hardware_device_obj.objects.filter(
                device_states__uuid=form_state
            ).first()

            if form_state and not device_state:
                self.add_error(
                    state_field,
                    error_message,
                )

            self.state_uuid = form_state
        except Exception:
            pass

        return clean

    def save(self, commit=True):
        """Attached custom field values and link to source event"""
        self.instance.event = models.Event.objects.get(uuid=self.event_uuid)
        self.instance.device_state = apps.get_model(
            "devices", "DeviceState"
        ).objects.get(uuid=self.state_uuid)
        super().save(commit=commit)


class EventResponseUpdateForm(EventResponseForm):
    """Overrides device form field to only show the name - user cannot select"""

    _device = forms.Field(label="Device", disabled=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # this lets super() know to disable device validation and take device from form kwargs
        self.is_update_form = True
