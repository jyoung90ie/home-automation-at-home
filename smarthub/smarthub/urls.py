from django.conf.urls import include
from django.contrib import admin
from django.urls import path

import debug_toolbar

urlpatterns = [
    # path("zigbee/", include("apps.zigbee.urls")),
    # path("api/", include("apps.api.urls")),
    path("", include("apps.pages.urls")),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("apps.users.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("devices/", include("apps.devices.urls")),
    path("admin/", admin.site.urls),
    path("__debug__/", include(debug_toolbar.urls)),
]
