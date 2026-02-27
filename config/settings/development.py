"""
Development settings — SQLite, local media, debug toolbar friendly.
"""

from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Disable template caching so on-disk edits appear immediately
TEMPLATES[0]["OPTIONS"]["debug"] = True  # noqa: F405

# ── Database (SQLite for zero-setup local dev) ────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
