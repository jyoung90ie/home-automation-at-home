# pylint: skip-file
from .settings import *

TEST_MODE = True
SECRET_KEY = "TESTMODE"

DATABASES = {
    "default": dj_database_url.config(default="postgis://postgres@localhost:5433/test")
}
