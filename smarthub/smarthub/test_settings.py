from .settings import *

TEST_MODE = True
SECRET_KEY = "TESTMODE"
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = "test"
DB_HOST = "db"
DATABASES["default"] = dj_database_url.config(
    default=f"postgis://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"
)
