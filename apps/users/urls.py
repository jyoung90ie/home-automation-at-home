from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("", views.AccountsRedirectView.as_view()),
    path("social/", views.AccountsSocialRedirectView.as_view()),
    path("password/", views.AccountsPasswordRedirectView.as_view()),
    path("profile/", views.profile, name="account_profile"),
]
