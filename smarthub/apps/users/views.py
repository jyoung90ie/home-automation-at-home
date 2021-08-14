from django.urls.base import reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth import get_user_model
import logging

from django.views.generic.base import RedirectView

logger = logging.getLogger(__name__)

# Create your views here.
class Profile(UpdateView):
    model = get_user_model()
    fields = ["first_name", "last_name", "home_location"]
    template_name = "users/profile.html"

    def __init__(self, **kwargs) -> None:
        logger.info(f"REQUEST OBJ: {self}")
        logger.info(f"DIR: {dir(self)}")
        super().__init__(**kwargs)

    def get_object(self, queryset=None):
        logger.info(f"REQUEST OBJ: {self.request}")
        logger.info(f"DIR: {dir(self.request)}")
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
