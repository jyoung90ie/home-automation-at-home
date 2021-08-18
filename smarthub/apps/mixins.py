"""Generalised CBV mixins for adding shared functionality"""
from django.contrib.auth.mixins import LoginRequiredMixin


class MakeRequestObjectAvailableInFormMixin:
    """Passes request object into form to enable custom queries"""

    def get_form_kwargs(self):
        """Update dict to include request object for access through form"""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class AddUserToFormMixin:
    """Adds user to form when validated - enables user to be stored on object creation"""

    def form_valid(self, form):
        """Add user via existing method"""
        form.instance.user = self.request.user
        return super().form_valid(form)


class LimitResultsToUserMixin(LoginRequiredMixin):
    """Override queryset to only show results for current user. This prevents user from
    accessing objects they do not own."""

    def get_queryset(self):
        """Append additional filter to given queryset"""
        return super().get_queryset().filter(user=self.request.user)
