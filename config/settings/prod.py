from .base import *  # noqa
import os

DEBUG = False

ALLOWED_HOSTS = ['epetcare.onrender.com', '.onrender.com']
host = os.environ.get('ALLOWED_HOST')
if host:
    ALLOWED_HOSTS.append(host)

# Static files configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration for Render
MEDIA_ROOT = '/opt/render/project/src/media'
MEDIA_URL = '/media/'

# Ensure media directory exists and is writable
import os
os.makedirs(MEDIA_ROOT, exist_ok=True)
# Ensure pet_images directory exists
os.makedirs(os.path.join(MEDIA_ROOT, 'pet_images'), exist_ok=True)

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() in ('1', 'true', 'yes')
