"""Custom forms"""
from typing import Optional

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Fieldset, Layout, Row, Submit
from django import forms
from django.urls import reverse

from . import models


class NotificationSettingForm(forms.ModelForm):
    """Setup user notifications"""

    access_token = forms.CharField(
        max_length=60, label="Pushbullet account API token", required=False
    )
    from_email = forms.EmailField(label="From Email", required=False)
    to_email = forms.EmailField(label="To Email", required=False)

    class Meta:
        model = models.NotificationSetting
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
                Field("notification_medium"),
                Field(
                    "is_enabled",
                    title="Do you want to enable notifications from this channel?",
                ),
            ),
            Row(
                Fieldset(
                    "Pushbullet Notification Setup",
                    "access_token",
                ),
                css_class="pushbullet-notification-setup d-none",
            ),
            Row(
                Fieldset(
                    "Email Notification Setup",
                    "from_email",
                    "to_email",
                ),
                css_class="email-notification-setup",
            ),
        )

        self.helper.add_input(Submit("submit", "Save", css_class="btn btn-primary"))

    def is_valid(self) -> bool:
        main_form = super().is_valid()  # must call here to get access to cleaned_data
        notification_settings: Optional(
            PushbulletNotificationForm, EmailNotificationForm
        )

        if self.cleaned_data["notification_medium"] == models.NotificationMedium.EMAIL:
            notification_settings = EmailNotificationForm(
                data={
                    "from_email": self.cleaned_data["from_email"],
                    "to_email": self.cleaned_data["to_email"],
                }
            )

        elif (
            self.cleaned_data["notification_medium"]
            == models.NotificationMedium.PUSHBULLET
        ):
            notification_settings = PushbulletNotificationForm(
                data={"access_token": self.cleaned_data["access_token"]}
            )

        if not notification_settings.is_valid():
            self.errors.update(notification_settings.errors)
            return False

        return main_form

    def save(self, commit=True):
        notification_medium = self.cleaned_data["notification_medium"]
        user = self.instance.user

        notification = models.NotificationSetting(
            user=user,
            notification_medium=notification_medium,
            is_enabled=self.cleaned_data["is_enabled"],
        )

        if commit:
            notification.save()

            if notification_medium == models.NotificationMedium.EMAIL:
                notification_settings = models.EmailNotification(
                    notification=notification,
                    from_email=self.cleaned_data["from_email"],
                    to_email=self.cleaned_data["to_email"],
                )

            elif notification_medium == models.NotificationMedium.PUSHBULLET:
                notification_settings = models.PushbulletNotification(
                    notification=notification,
                    access_token=self.cleaned_data["access_token"],
                )

            notification_settings.save()

        return self.instance


class UpdateNotificationSettingForm(forms.ModelForm):
    """Setup user notifications"""

    notification_medium = forms.CharField(label="Notification medium")
    access_token = forms.CharField(
        max_length=60, label="Pushbullet account API token", required=False
    )
    from_email = forms.EmailField(label="From Email", required=False)
    to_email = forms.EmailField(label="To Email", required=False)

    class Meta:
        model = models.NotificationSetting
        fields = [
            "is_enabled",
            "access_token",
            "from_email",
            "to_email",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        uuid = getattr(kwargs["instance"], "uuid")

        self.user = getattr(request, "user", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "update_notification_channel"
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-5"
        self.helper.field_class = "col-md-7"
        self.helper.form_method = "post"
        self.helper.form_action = reverse(
            "notifications:notification:update", kwargs={"uuid": uuid}
        )

        self.helper.layout = Layout(
            Row(
                Field(
                    "notification_medium",
                    readonly="readonly",
                ),
                Field(
                    "is_enabled",
                    title="Do you want to enable notifications from this channel?",
                ),
            ),
            Row(
                Fieldset(
                    "Pushbullet Notification Setup",
                    "access_token",
                ),
                css_class="pushbullet-notification-setup d-none",
            ),
            Row(
                Fieldset(
                    "Email Notification Setup",
                    "from_email",
                    "to_email",
                ),
                css_class="email-notification-setup d-none",
            ),
        )

        self.helper.add_input(Submit("submit", "Update", css_class="btn btn-primary"))

    def is_valid(self) -> bool:
        try:
            super().is_valid()  # enables access to form cleaned_data
            notification_settings: Optional(
                PushbulletNotificationForm, EmailNotificationForm
            )

            if (
                self.cleaned_data["notification_medium"]
                == models.NotificationMedium.EMAIL
            ):
                notification_settings = EmailNotificationForm(
                    data={
                        "from_email": self.cleaned_data["from_email"],
                        "to_email": self.cleaned_data["to_email"],
                    }
                )

            elif (
                self.cleaned_data["notification_medium"]
                == models.NotificationMedium.PUSHBULLET
            ):
                notification_settings = PushbulletNotificationForm(
                    data={"access_token": self.cleaned_data["access_token"]}
                )

            return notification_settings.is_valid()
        except UnboundLocalError:
            # field was manually overridden - avoids error
            self.errors.update({"notification_medium": ["Invalid value"]})
            return False

    def save(self, commit=True):
        form = self.instance

        form.is_enabled = self.cleaned_data["is_enabled"]
        if commit:
            form.save()

        email = getattr(form, "emailnotification", False)
        pushbullet = getattr(form, "pushbulletnotification", False)

        if email:
            email.to_email = self.cleaned_data["to_email"]
            email.from_email = self.cleaned_data["from_email"]
            if commit:
                email.save()
        if pushbullet:
            pushbullet.access_token = self.cleaned_data["access_token"]
            if commit:
                pushbullet.save()

        return form


class PushbulletNotificationForm(forms.ModelForm):
    """Form is nevered directly invoked, but is used within another form to validate input
    fields"""

    class Meta:
        model = models.PushbulletNotification
        fields = ("access_token",)


class EmailNotificationForm(forms.ModelForm):
    """Form is nevered directly invoked, but is used within another form to validate input
    fields"""

    class Meta:
        model = models.EmailNotification
        fields = (
            "from_email",
            "to_email",
        )
