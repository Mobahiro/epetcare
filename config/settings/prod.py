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

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() in ('1', 'true', 'yes')
