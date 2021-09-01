""" URL endpoints for app """
from django.urls import include, path

from . import views

app_name = "mqtt"

urlpatterns = [
    path(
        "publish/<uuid:duuid>/",  # device uuid
        include(
            (
                [
                    path("toggle/", views.ToggleDeviceState.as_view(), name="toggle"),
                    path(
                        "trigger/", views.TriggerDeviceState.as_view(), name="trigger"
                    ),
                ],
                "publish",
            ),
        ),
    ),
]
