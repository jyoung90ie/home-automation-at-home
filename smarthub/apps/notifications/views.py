"""Handles notification page requests"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from ..mixins import (
    AddUserToFormMixin,
    LimitResultsToUserMixin,
    MakeRequestObjectAvailableInFormMixin,
)
from ..views import UUIDView
from . import forms, models


class AddNotificationSetting(
    LoginRequiredMixin,
    AddUserToFormMixin,
    MakeRequestObjectAvailableInFormMixin,
    CreateView,
):
    """Enables user to create new notifications.
    User can only create one setting per notification channel."""

    form_class = forms.NotificationSettingForm
    template_name = "notifications/notification_form.html"
    success_url = reverse_lazy("notifications:list")

    def form_valid(self, form):
        """Override default implemtation to check that user does not already have this channel
        setup"""
        kwargs = self.get_form_kwargs()
        request = kwargs["request"]
        notification_medium = form.cleaned_data["notification_medium"]

        try:
            form_valid = super().form_valid(form)
            messages.success(request, "New notification channel added")
            return form_valid
        except IntegrityError:
            messages.error(
                request,
                f"You have already setup a notification channel for {notification_medium} -"
                " you cannot create more than one per channel. Your existing settings can be"
                " updated by selecting below.",
            )
            return HttpResponseRedirect(reverse_lazy("notifications:list"))


class ListNotificationSetting(LimitResultsToUserMixin, ListView):
    """List all of the user's notification objects"""

    model = models.NotificationSetting
    context_object_name = "notifications"
    template_name = "notifications/notification_list.html"
    ordering = ["-is_enabled", "created_at"]


class UpdateNotificationSetting(LimitResultsToUserMixin, UUIDView, UpdateView):
    """Permit user to update their own notification objects"""

    form_class = forms.UpdateNotificationSettingForm
    template_name = "notifications/notification_update_form.html"

    def get_queryset(self):
        """Populate with user's notification settings only"""
        uuid = self.kwargs.get("uuid")
        user = self.request.user

        return models.NotificationSetting.objects.filter(user=user, uuid=uuid)

    def get_initial(self):
        """Pass through value for manual form field"""
        initial = super().get_initial()
        obj = self.get_object()
        initial["notification_medium"] = getattr(obj, "notification_medium", "")

        pushbullet = getattr(obj, "pushbulletnotification", False)
        email = getattr(obj, "emailnotification", False)

        if email:
            initial["from_email"] = getattr(email, "from_email", "")
            initial["to_email"] = getattr(email, "to_email", "")

        if pushbullet:
            initial["access_token"] = getattr(pushbullet, "access_token", "")
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Notification settings updated")
        return super().form_valid(form)


class DeleteNotificationSetting(LimitResultsToUserMixin, UUIDView, DeleteView):
    """Enables user to delete their own notification objects"""

    model = models.NotificationSetting
    success_url = reverse_lazy("notifications:list")
    template_name = "notifications/notification_confirm_delete.html"


class RedirectToNotificationList(RedirectView):
    """Redirects URL to proper update path - for breadcrumb"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy("notifications:list")
