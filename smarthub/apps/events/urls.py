""" URL endpoints for app """
from django.urls import include, path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.ListEvent.as_view(), name="list"),
    path("add/", views.AddEvent.as_view(), name="add"),
    path(
        "<uuid:uuid>/",
        include(
            (
                [
                    path("", views.DetailEvent.as_view(), name="detail"),
                    path("update/", views.UpdateEvent.as_view(), name="update"),
                    path("delete/", views.DeleteEvent.as_view(), name="delete"),
                ],
                "event",
            ),
        ),
    ),
]
