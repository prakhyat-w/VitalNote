"""
Base settings shared across all environments.
Environment-specific settings live in development.py and production.py.
"""

import os
import ssl
from pathlib import Path

import environ

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Environment ───────────────────────────────────────────────────────────────
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# ── Application definition ────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "storages",
    # Local
    "apps.users",
    "apps.encounters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# ── Password validation ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Custom User model ─────────────────────────────────────────────────────────
AUTH_USER_MODEL = "users.User"

# ── Auth redirects ────────────────────────────────────────────────────────────
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ── Media files ───────────────────────────────────────────────────────────────
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── File upload limits ────────────────────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 26_214_400   # 25 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 26_214_400   # 25 MB

# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ── drf-spectacular ───────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "VitalNote API",
    "DESCRIPTION": (
        "Medical AI Scribe — upload audio consultations, get transcription, "
        "PII redaction, and a structured SOAP note."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True

# Upstash uses TLS (rediss://): tell Celery to accept the managed certificate.
if CELERY_BROKER_URL.startswith("rediss://"):
    _ssl_opts = {"ssl_cert_reqs": ssl.CERT_NONE}
    CELERY_BROKER_USE_SSL = _ssl_opts
    CELERY_REDIS_BACKEND_USE_SSL = _ssl_opts

# ── External API keys ─────────────────────────────────────────────────────────
ASSEMBLYAI_API_KEY = env("ASSEMBLYAI_API_KEY", default="")
GROQ_API_KEY = env("GROQ_API_KEY", default="")

# ── Cloudflare R2 (S3-compatible storage) ────────────────────────────────────
USE_R2 = env.bool("USE_R2", default=False)

if USE_R2:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }
    AWS_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("R2_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = env("R2_ENDPOINT_URL")
    AWS_S3_REGION_NAME = "auto"
    AWS_DEFAULT_ACL = "private"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = True  # Always use pre-signed URLs
