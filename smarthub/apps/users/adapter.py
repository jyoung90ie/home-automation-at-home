import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.utils import SERIALIZED_DB_FIELD_PREFIX
from django.contrib.auth import get_user_model
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """Override default implementation"""


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Override default implementation for customised user fields"""

    def __init__(self, request):
        super().__init__(request=request)

    def pre_social_login(self, request, sociallogin):
        """Connect social account to existing account, if existing email found"""

        if sociallogin.is_existing:
            return

        email_addresses = sociallogin.email_addresses

        for email in email_addresses:
            try:
                user_email = EmailAddress.objects.get(email__iexact=email.email)
            except EmailAddress.DoesNotExist:
                continue

            user = user_email.user
            sociallogin.connect(request, user)
