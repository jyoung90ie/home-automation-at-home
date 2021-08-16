from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from . import models
from django import forms


class NotificationForm(forms.ModelForm):
    """Setup user notifications"""

    access_token = forms.CharField(
        max_length=60, label="Pushbullet account API token", required=False
    )
    from_email = forms.EmailField(label="Send from", required=False)
    to_email = forms.EmailField(label="Send to", required=False)

    class Meta:
        model = models.UserNotificationSetting
        fields = [
            "notification_medium",
            "is_enabled",
            "access_token",
            "from_email",
            "to_email",
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
        self.helper.form_action = "notifications:add"

        self.helper.layout = Layout(
            Row(
                Column(
                    Field("notification_medium", css_class="col-md-6 mb-0"),
                    Field("is_enabled"),
                    Field("access_token", type="hidden"),
                    css_class="col-md-6",
                ),
            ),
            Row(
                Column(Field("from_email", type="hidden"), css_class="col-md-6"),
                Column(
                    Field("to_email", type="hidden"),
                    css_class="col-md-6",
                ),
            ),
        )

        self.helper.add_input(
            Submit("submit", "Create Notification", css_class="btn btn-primary")
        )
