from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-your-secret-key-change-in-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

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

# Try to import dj_database_url for production, use SQLite for development

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== STRIPE CONFIGURATION =====
STRIPE_PUBLIC_KEY = "pk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"
STRIPE_SECRET_KEY = "sk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"

# ===== SECURITY SETTINGS =====
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ===== SESSION TIMEOUT (10 minutes of inactivity) =====
SESSION_COOKIE_AGE = 600  # 10 minutes in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Update session time on every request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Also expire on browser close
