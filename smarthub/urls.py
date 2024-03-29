from django.conf.urls import include
from django.contrib import admin
from django.urls import path

import debug_toolbar

urlpatterns = [
    path("", include("apps.pages.urls")),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("apps.users.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("devices/", include("apps.devices.urls")),
    path("events/", include("apps.events.urls")),
    path("mqtt/", include("apps.mqtt.urls")),
    path("admin/", admin.site.urls),
    path("__debug__/", include(debug_toolbar.urls)),
]
