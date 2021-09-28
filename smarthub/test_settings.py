# pylint: skip-file
from .settings import *

TEST_MODE = True
SECRET_KEY = "TESTMODE"

DATABASES = {
    "default": dj_database_url.config(
        default="postgis://smarthub:smarthub@db:5432/test"
    )
}

# prevent test errors from static files
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
