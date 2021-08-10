import debug_toolbar
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    # path("zigbee/", include("zigbee.urls")),
    # path("api/", include("api.urls")),
    path("", include("pages.urls")),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("users.urls")),
    path("devices/", include("devices.urls")),
    path("admin/", admin.site.urls),
    path("__debug__/", include(debug_toolbar.urls)),
]
