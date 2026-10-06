import os
from dotenv import load_dotenv

load_dotenv()


def _environment_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    APP_ENV = os.getenv("APP_ENV", "local").strip().lower()
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOCAL_DEMO_MODE = APP_ENV in {"local", "development", "demo"}
    DEBUG = _environment_flag(
        "FLASK_DEBUG",
        default=APP_ENV == "development"
    )
    DEMO_OTP_ENABLED = (
        LOCAL_DEMO_MODE
        and _environment_flag("DEMO_OTP_ENABLED", default=True)
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _environment_flag(
        "SESSION_COOKIE_SECURE",
        default=not LOCAL_DEMO_MODE
    )