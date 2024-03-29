""" URL endpoints for app """
from django.urls import include, path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.ListEvents.as_view(), name="list"),
    path("add/", views.AddEvent.as_view(), name="add"),
    path(
        "<uuid:uuid>/",
        include(
            (
                [
                    path("", views.DetailEvent.as_view(), name="detail"),
                    path("update/", views.UpdateEvent.as_view(), name="update"),
                    path("delete/", views.DeleteEvent.as_view(), name="delete"),
                    path(
                        "trigger/",
                        include(
                            (
                                [
                                    path("", views.EventDetailRedirectView.as_view()),
                                    path(
                                        "add/",
                                        views.AddEventTrigger.as_view(),
                                        name="add",
                                    ),
                                    path(
                                        "<uuid:tuuid>/",
                                        include(
                                            (
                                                [
                                                    path(
                                                        "",
                                                        views.EventTriggerRedirectView.as_view(),
                                                    ),
                                                    path(
                                                        "update/",
                                                        views.UpdateEventTrigger.as_view(),
                                                        name="update",
                                                    ),
                                                    path(
                                                        "delete/",
                                                        views.DeleteEventTrigger.as_view(),
                                                        name="delete",
                                                    ),
                                                ],
                                                "trigger",
                                            ),
                                        ),
                                    ),
                                ],
                                "triggers",
                            )
                        ),
                    ),
                    path(
                        "response/",
                        include(
                            (
                                [
                                    path("", views.EventDetailRedirectView.as_view()),
                                    path(
                                        "add/",
                                        views.AddEventResponse.as_view(),
                                        name="add",
                                    ),
                                    path(
                                        "<uuid:ruuid>/",
                                        include(
                                            (
                                                [
                                                    path(
                                                        "",
                                                        views.EventResponseRedirectView.as_view(),
                                                    ),
                                                    path(
                                                        "update/",
                                                        views.UpdateEventResponse.as_view(),
                                                        name="update",
                                                    ),
                                                    path(
                                                        "delete/",
                                                        views.DeleteEventResponse.as_view(),
                                                        name="delete",
                                                    ),
                                                ],
                                                "response",
                                            ),
                                        ),
                                    ),
                                ],
                                "responses",
                            )
                        ),
                    ),
                ],
                "event",
            ),
        ),
    ),
]
