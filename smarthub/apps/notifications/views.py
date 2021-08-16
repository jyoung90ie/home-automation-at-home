from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from . import models, forms


class AddNotificationMedium(LoginRequiredMixin, CreateView):
    form_class = forms.NotificationForm
    template_name = "notifications/notification_form.html"
    success_url = reverse_lazy("notifications:list")


class ListNotificationMediums(LoginRequiredMixin, ListView):
    model = models.UserNotificationSetting
    context_object_name = "notifications"
    template_name = "notifications/notification_list.html"
    ordering = ["is_enabled", "created_at"]
