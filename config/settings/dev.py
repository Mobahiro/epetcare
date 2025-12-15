from .base import *  # noqa
import os

DEBUG = True

ALLOWED_HOSTS = ['*']

# Local static files storage
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# If an external DATABASE_URL is provided (e.g., Render Postgres), use it.
# Otherwise, fall back to local SQLite for convenience.
if not os.environ.get('DATABASE_URL'):
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.sqlite3',
			'NAME': BASE_DIR / 'db.sqlite3',
		}
	}

# Email settings for development
# Default to console backend (prints emails in terminal)
# You can override to SMTP (e.g., Gmail) by setting these in your local .env
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '0')) or None
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').lower() in ('1', 'true', 'yes')
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '15'))
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ePetCare <no-reply@localhost>')

# If an HTTP email provider is configured (e.g., SendGrid), prefer it and avoid SMTP
if os.environ.get('EMAIL_HTTP_PROVIDER', '').strip():
	EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Branding (optional) for emails/templates
BRAND_NAME = os.environ.get('BRAND_NAME', 'ePetCare')
EMAIL_BRAND_LOGO_URL = os.environ.get('EMAIL_BRAND_LOGO_URL', '')  # e.g., https://epetcare.onrender.com/static/clinic/images/logo.png

# Allow login with either username or email
AUTHENTICATION_BACKENDS = [
	'clinic.auth_backends.EmailOrUsernameModelBackend',
	'django.contrib.auth.backends.ModelBackend',
]

# Enhanced logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'clinic': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
