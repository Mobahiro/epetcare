from .base import *  # noqa
import os
import sys

# Set DEBUG to True temporarily to get detailed error pages
# Remember to set back to False after debugging
DEBUG = os.environ.get('DEBUG', 'false').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['epetcare.onrender.com', '.onrender.com']
host = os.environ.get('ALLOWED_HOST')
if host:
    ALLOWED_HOSTS.append(host)

# CSRF trusted origins for Render
CSRF_TRUSTED_ORIGINS = [
    'https://epetcare.onrender.com',
]
extra_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if extra_csrf:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in extra_csrf.split(',') if o.strip()]

# Static files configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration for Render
MEDIA_ROOT = '/opt/render/project/src/media'
MEDIA_URL = '/media/'

# Enhanced logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout,
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/opt/render/project/src/logs/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'clinic': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Ensure necessary directories exist
import os
try:
    # Ensure logs directory exists
    os.makedirs('/opt/render/project/src/logs', exist_ok=True)

    # Ensure media directory exists and is writable
    os.makedirs(MEDIA_ROOT, exist_ok=True)

    # Ensure pet_images directory exists
    os.makedirs(os.path.join(MEDIA_ROOT, 'pet_images'), exist_ok=True)

    # Make sure media directories are writable
    os.chmod(MEDIA_ROOT, 0o777)
    os.chmod(os.path.join(MEDIA_ROOT, 'pet_images'), 0o777)
except Exception as e:
    print(f"Error creating directories: {e}")
    # Continue anyway - don't crash the server startup

"""Email configuration
Prefer SMTP if fully configured via environment variables; otherwise fall back to
console backend to avoid 500s in production when emails are not yet set up.
"""
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587')) if os.environ.get('EMAIL_PORT') else None
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').lower() in ('1', 'true', 'yes')
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ePetCare <no-reply@epetcare.onrender.com>')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

# Auto-fallback to console backend if SMTP host or credentials are missing
if EMAIL_BACKEND.endswith('smtp.EmailBackend'):
    if not EMAIL_HOST or not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() in ('1', 'true', 'yes')
