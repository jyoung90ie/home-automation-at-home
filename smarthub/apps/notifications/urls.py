from django.conf.urls import include
from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.ListNotificationSetting.as_view(), name="list"),
    path("add/", views.AddNotificationSetting.as_view(), name="add"),
    path(
        "<uuid:uuid>/",
        include(
            (
                [
                    path("", views.RedirectToNotificationList.as_view()),
                    path(
                        "update/",
                        views.UpdateNotificationSetting.as_view(),
                        name="update",
                    ),
                    path(
                        "delete/",
                        views.DeleteNotificationSetting.as_view(),
                        name="delete",
                    ),
                ],
                "notification",
            ),
        ),
    ),
]
