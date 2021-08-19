"""Generalised CBV mixins for adding shared functionality"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse


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


class UserHasLinkedDevice:
    """User must have at least one device that has been linked to a hardware device
    before they will be permitted to access the view"""

    def get(self, request, *args, **kwargs):
        """Intercept default functionality to check for user devices - if don't exist then
        redirect user to devices page - otherwise continue as normal"""
        user = request.user

        total_linked_devices = user.total_linked_devices

        print("total_linked_devices", total_linked_devices)
        print("total_linked_devices", dir(total_linked_devices))

        if total_linked_devices == 0:
            messages.warning(
                request,
                "You need at least one device, that has been linked to a"
                " hardware device and is recording data, before you can access that view.",
            )
            return HttpResponseRedirect(reverse("devices:list"))

        return super().get(self, request, *args, **kwargs)
