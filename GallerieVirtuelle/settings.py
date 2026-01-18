from pathlib import Path
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-this-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

AUTH_USER_MODEL = "galerie.Utilisateur"

LOGIN_URL = "galerie:login"
LOGIN_REDIRECT_URL = "galerie:home"
LOGOUT_REDIRECT_URL = "galerie:home"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "galerie",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # WhiteNoise for static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "GallerieVirtuelle.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
import dj_database_url

# Use DATABASE_URL for production, SQLite for development
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )   "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WSGI_APPLICATION = "GallerieVirtuelle.wsgi.application"

STATIC_URL = "/static/"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZenvironment variables for production
STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="pk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="sk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx")

# ===== SECURITY SETTINGS =====
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)

# ===== STRIPE CONFIGURATION =====
# Use test keys for development
STRIPE_PUBLIC_KEY = "pk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"
STRIPE_SECRET_KEY = "sk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"
