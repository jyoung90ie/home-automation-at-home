""" URL endpoints for app """
from django.urls import include, path

from . import views

app_name = "mqtt"

urlpatterns = [
    path(
        "publish/",  # device uuid
        include(
            (
                [
                    path(
                        "<uuid:duuid>/toggle/",
                        views.ToggleDeviceState.as_view(),
                        name="toggle",
                    ),
                    path(
                        "<uuid:suuid>/trigger/",
                        views.TriggerDeviceState.as_view(),
                        name="trigger",
                    ),
                ],
                "publish",
            ),
        ),
    ),
]
