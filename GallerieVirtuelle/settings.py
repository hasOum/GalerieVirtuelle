from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "..."
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

WSGI_APPLICATION = "GallerieVirtuelle.wsgi.application"

STATIC_URL = "/static/"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== STRIPE CONFIGURATION =====
# Use test keys for development
STRIPE_PUBLIC_KEY = "pk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"
STRIPE_SECRET_KEY = "sk_test_51QxU3IB9WXO5yyKDUZ5lQX9zQNqK1ZqQ0YzFxmXxLqXxLqXxLqXxLqXx"
