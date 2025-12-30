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

# Brevo (Sendinblue) SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'ePetCare <epetcarewebsystem@gmail.com>'
EMAIL_TIMEOUT = 30
SERVER_EMAIL = 'epetcarewebsystem@gmail.com'

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
