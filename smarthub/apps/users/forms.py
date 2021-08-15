from django.contrib.auth import get_user_model
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Submit, Field, Div, Row


class SignupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "signup_form"
        self.helper.form_method = "post"
        self.helper.form_action = "account_signup"

        self.helper.layout = Layout(
            "email",
            Row(
                Column("password1", css_class="form-group col-md-6 mb-0"),
                Column("password2", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            Row(Column("home_location", css_class="form-group col-md-6 mb-4")),
        )

        self.helper.add_input(Submit("submit", "Register", css_class="mb-5"))

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "home_location"]

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.home_location = self.cleaned_data["home_location"]
        user.save()


class UpdateProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id_update_profile_form"
        self.helper.form_method = "post"
        self.helper.form_action = "users:account_profile"

        self.helper.layout = Layout(
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            Row(Column("home_location", css_class="form-group col-md-6 mb-4")),
        )

        self.helper.add_input(Submit("submit", "Update", css_class="mb-5"))

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "home_location"]
