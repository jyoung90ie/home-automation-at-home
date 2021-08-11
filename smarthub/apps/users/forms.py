from django.contrib.auth import get_user_model
from django import forms


class SignupForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "home_location"]

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.home_location = self.cleaned_data["home_location"]
        user.save()
