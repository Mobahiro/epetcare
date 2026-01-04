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
# Use Django's basic storage - WhiteNoise middleware handles serving efficiently
# Avoid WhiteNoise storage backends as they have race conditions during collectstatic
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Cloudinary configuration for persistent media storage
# Render has ephemeral storage - files are lost on restart
# Cloudinary provides persistent cloud storage for media files
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
}

# Use Cloudinary for media files if configured, otherwise fall back to local storage
if CLOUDINARY_STORAGE['CLOUD_NAME'] and CLOUDINARY_STORAGE['API_KEY'] and CLOUDINARY_STORAGE['API_SECRET']:
    # Add cloudinary_storage to installed apps
    INSTALLED_APPS = ['cloudinary_storage', 'cloudinary'] + INSTALLED_APPS
    # Django 6.0+ uses STORAGES instead of DEFAULT_FILE_STORAGE
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = '/media/'  # Cloudinary will handle the actual URL
    print("Cloudinary storage enabled for media files")
else:
    # Fallback to local storage (files will be lost on Render restart)
    MEDIA_ROOT = '/opt/render/project/src/media'
    MEDIA_URL = '/media/'
    print("WARNING: Cloudinary not configured - using local storage (files will be lost on restart)")

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
EMAIL_FROM_ADDRESS = os.environ.get('EMAIL_FROM_ADDRESS', '').strip()
EMAIL_FROM_NAME = os.environ.get('EMAIL_FROM_NAME', os.environ.get('BRAND_NAME', 'ePetCare')).strip() or 'ePetCare'
DEFAULT_FROM_EMAIL = (
    f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>" if EMAIL_FROM_ADDRESS else os.environ.get('DEFAULT_FROM_EMAIL', f"{EMAIL_FROM_NAME} <no-reply@epetcare.onrender.com>")
)
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

# Log a deliverability warning when using the default onrender.com sender
try:
    from email.utils import parseaddr
    display, addr = parseaddr(DEFAULT_FROM_EMAIL)
    domain = (addr.split('@', 1)[1] if '@' in addr else '').lower()
    if domain.endswith('onrender.com'):
        import logging
        logging.getLogger('clinic').warning(
            'DEFAULT_FROM_EMAIL is using %s which is rarely authenticated. '
            'Set EMAIL_FROM_ADDRESS to a verified domain (e.g., no-reply@yourdomain.com) and '
            'complete SPF/DKIM/DMARC with your provider to prevent spam folder.',
            domain
        )
except Exception:
    pass

# Auto-fallback to console backend if SMTP host or credentials are missing
if EMAIL_BACKEND.endswith('smtp.EmailBackend'):
    if not EMAIL_HOST or not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow forcing console backend to avoid SMTP on platforms that block it
if os.environ.get('EMAIL_FORCE_CONSOLE', 'false').lower() in ('1', 'true', 'yes'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# If an HTTP email provider is configured, prefer it and disable SMTP by using console backend
if os.environ.get('EMAIL_HTTP_PROVIDER', '').strip():
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() in ('1', 'true', 'yes')

# Allow login with either username or email
AUTHENTICATION_BACKENDS = [
    'clinic.auth_backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Branding (optional) for emails/templates
BRAND_NAME = os.environ.get('BRAND_NAME', 'ePetCare')
EMAIL_BRAND_LOGO_URL = os.environ.get('EMAIL_BRAND_LOGO_URL', '')  # e.g., https://epetcare.onrender.com/static/clinic/images/logo.png
