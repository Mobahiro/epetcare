"""
Production settings for epetcare project deployed on Render.
These settings override or extend the base settings.py.
"""

import os
import dj_database_url
from pathlib import Path
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Get the SECRET_KEY from environment variable
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# Allow the Render host domain
ALLOWED_HOSTS = [
    '.onrender.com',  # Render domains
    os.environ.get('ALLOWED_HOST', '*'),  # Custom domain if set up
]

# Use HTTPS for secure cookies and more
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Use PostgreSQL database on Render
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional security settings
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True