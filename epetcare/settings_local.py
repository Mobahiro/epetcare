"""
Local development settings for epetcare project.
This file overrides settings.py for local development.

Usage:
    export DJANGO_SETTINGS_MODULE=epetcare.settings_local
    python manage.py runserver
"""

from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=(2hy%htsi*&@2f(#x2tot4m%&3g(68=n%kpe-cd%_kfxa78(%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Force IS_PRODUCTION to False for local development
IS_PRODUCTION = False

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable whitenoise storage in development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Add localhost to allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1']