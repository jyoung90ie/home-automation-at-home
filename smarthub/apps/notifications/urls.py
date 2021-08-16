from django.conf.urls import include
from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.ListNotificationMediums.as_view(), name="list"),
    path("add/", views.AddNotificationMedium.as_view(), name="add"),
    path(
        "<uuid:uuid>/",
        include(
            (
                [
                    path(
                        "update/",
                        views.ListNotificationMediums.as_view(),
                        name="update",
                    ),
                    path(
                        "delete/",
                        views.ListNotificationMediums.as_view(),
                        name="delete",
                    ),
                ],
                "notification",
            ),
        ),
    ),
]
