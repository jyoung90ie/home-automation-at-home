from django.urls import path

from . import views

urlpatterns = [
    path("", views.Home.as_view(), name="homepage"),
    path("about/", views.About.as_view(), name="about"),
    path("help/", views.Help.as_view(), name="help"),
]
