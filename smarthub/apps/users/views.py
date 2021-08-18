import logging

from django.contrib.auth import get_user_model
from django.urls.base import reverse_lazy
from django.views.generic import UpdateView
from django.views.generic.base import RedirectView

from . import forms

logger = logging.getLogger(__name__)


class Profile(UpdateView):
    form_class = forms.UpdateProfileForm
    template_name = "users/profile.html"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get_object(self, queryset=None):
        return self.request.user


profile = Profile.as_view()


class AccountsRedirectView(RedirectView):
    """Redirects to specified page for non-existant breadcrumbs"""

    url = reverse_lazy("users:account_profile")


class AccountsPasswordRedirectView(RedirectView):
    """Redirects to specified page for non-existant breadcrumbs"""

    url = reverse_lazy("account_change_password")


class AccountsSocialRedirectView(RedirectView):
    """Redirects to specified page for non-existant breadcrumbs"""

    url = reverse_lazy("socialaccount_connections")
