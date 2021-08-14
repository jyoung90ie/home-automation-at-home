from django.conf.urls import include
from django.urls import path, include

from . import views

app_name = "devices"

urlpatterns = [
    path("", views.ListDevices.as_view(), name="list"),
    path("add/", views.AddDevice.as_view(), name="add"),
    path(
        "<uuid:uuid>/",
        include(
            (
                [
                    path("", views.DetailDevice.as_view(), name="detail"),
                    path("update", views.UpdateDevice.as_view(), name="update"),
                    path("delete", views.DeleteDevice.as_view(), name="delete"),
                    path("logs", views.LogsForDevice.as_view(), name="logs"),
                ],
                "device",
            ),
        ),
    ),
    path(
        "locations/",
        include(
            (
                [
                    path("", views.ListDeviceLocations.as_view(), name="list"),
                    path(
                        "<uuid:uuid>/",
                        include(
                            [
                                path(
                                    "update/",
                                    views.UpdateDeviceLocation.as_view(),
                                    name="update",
                                ),
                                path(
                                    "delete",
                                    views.DeleteDeviceLocation.as_view(),
                                    name="delete",
                                ),
                            ]
                        ),
                    ),
                    path("add", views.AddDeviceLocation.as_view(), name="add"),
                ],
                "locations",
            )
        ),
    ),
]
