"""Custom forms for handling creation of events with event trigger objects"""

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Fieldset, Layout, Row, Submit

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

    # def save(self, commit):
    #     """Override default implementation to save multiple models are once
    #     i.e. Event and (n)EventTriggers"""
    #     return super().save(commit=commit)
