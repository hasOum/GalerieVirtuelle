from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Try to import decouple, but make it optional for local development
try:
    from decouple import config
except ImportError:
    def config(key, default=None, cast=bool):
        """Fallback config function when decouple is not installed"""
        return os.getenv(key, default)

SECRET_KEY = config("SECRET_KEY", default="django-insecure-your-secret-key-change-in-production")
DEBUG = config("DEBUG", default=True)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

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
]

# Add WhiteNoise only if available (for production)
try:
    import whitenoise
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
except ImportError:
    pass

# Continue with other middleware
MIDDLEWARE.extend([
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
])

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
try:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600
        )
    }
except ImportError:
    # Fallback to SQLite for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Use WhiteNoise storage only if available (for production)
try:
    import whitenoise
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
except ImportError:
    pass

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== STRIPE CONFIGURATION =====
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "pk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx")

# ===== SECURITY SETTINGS =====
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False").lower() == "true"
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)

# ===== STRIPE CONFIGURATION =====
# Use test keys for development
STRIPE_PUBLIC_KEY = "pk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"
STRIPE_SECRET_KEY = "sk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"
