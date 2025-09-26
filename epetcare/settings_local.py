"""
Local development settings for epetcare project.
This file overrides settings.py for local development.

Usage:
    export DJANGO_SETTINGS_MODULE=epetcare.settings_local
    python manage.py runserver
"""

from .settings import *  # noqa

# Local overrides (PostgreSQL enforced in base settings).
DEBUG = True
IS_PRODUCTION = False

# Allow local hosts
ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

# Static files: use default storage locally (already set in base when not production)