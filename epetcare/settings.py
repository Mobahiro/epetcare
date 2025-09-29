
import os
from pathlib import Path
import warnings
import dj_database_url
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# Check if we're on Render.com (production)
IS_PRODUCTION = os.environ.get('RENDER', '') == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
def generate_secret_key():
    """Generate a secure secret key that is different for each environment"""
    from django.core.management.utils import get_random_secret_key
    return get_random_secret_key()

# Use SECRET_KEY from environment, or generate a secure one
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    # This ensures a unique but stable key for development 
    # but forces use of environment variable in production
    if IS_PRODUCTION:
        raise ValueError('SECRET_KEY environment variable is required in production')
    SECRET_KEY = generate_secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
# Turn off debug in production
DEBUG = not IS_PRODUCTION

# Add render.com domain to allowed hosts for production
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
if IS_PRODUCTION:
    ALLOWED_HOSTS.extend(['epetcare.onrender.com', '.onrender.com'])


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'clinic',
    'vet',
    'vet_portal',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add whitenoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'epetcare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'epetcare.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://shiro:AfsXuq5zLnQMRn0iFSAxxIV4tYB8tYnG@dpg-d3an6aggjchc73cpr5i0-a/epetcare_database').strip()

def _build_postgres_from_parts():
    name = os.environ.get('POSTGRES_DB') or os.environ.get('PGDATABASE')
    user = os.environ.get('POSTGRES_USER') or os.environ.get('PGUSER')
    password = os.environ.get('POSTGRES_PASSWORD') or os.environ.get('PGPASSWORD')
    host = os.environ.get('POSTGRES_HOST') or os.environ.get('PGHOST') or 'localhost'
    port = os.environ.get('POSTGRES_PORT') or os.environ.get('PGPORT') or '5432'

    missing = [k for k, v in {
        'POSTGRES_DB/PGDATABASE': name,
        'POSTGRES_USER/PGUSER': user,
        'POSTGRES_PASSWORD/PGPASSWORD': password,
    }.items() if not v]

    if missing:
        raise RuntimeError(
            "PostgreSQL is required but configuration is incomplete. Set DATABASE_URL or the env vars: "
            + ", ".join(missing)
        )

    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': name,
        'USER': user,
        'PASSWORD': password,
        'HOST': host,
        'PORT': port,
    }

def _apply_common_db_options(cfg: dict) -> dict:
    conn_max_age = int(os.environ.get('DB_CONN_MAX_AGE', '600'))
    cfg['CONN_MAX_AGE'] = conn_max_age

    # SSL options (useful on managed services)
    ssl_require = os.environ.get('DB_SSL_REQUIRE', '').lower() in ('1', 'true', 'yes')
    sslmode = os.environ.get('DB_SSLMODE', 'require' if ssl_require else '')
    sslrootcert = os.environ.get('DB_SSLROOTCERT', '')

    options = cfg.setdefault('OPTIONS', {})
    if ssl_require or sslmode:
        options['sslmode'] = sslmode or 'require'
    if sslrootcert:
        options['sslrootcert'] = sslrootcert

    # Test database name
    test_name = os.environ.get('POSTGRES_TEST_DB')
    if test_name:
        cfg['TEST'] = {'NAME': test_name}
    else:
        # Django will derive NAME + '_test' automatically; keep explicit for clarity
        cfg['TEST'] = {'NAME': f"{cfg.get('NAME', 'test')}_test"}

    return cfg

def _postgres_from_url(url: str) -> dict:
    # Validate scheme first to avoid silently accepting sqlite or other engines
    lowered = url.lower()
    valid_prefixes = (
        'postgres://',
        'postgresql://',
        'postgresql+psycopg2://',
    )
    if not lowered.startswith(valid_prefixes):
        raise RuntimeError(
            "DATABASE_URL must start with postgres://, postgresql://, or postgresql+psycopg2://"
        )
    # Parse with dj_database_url, then force engine to Django's postgres backend
    cfg = dj_database_url.parse(url)
    cfg['ENGINE'] = 'django.db.backends.postgresql'
    return cfg

DATABASES = {}

try:
    if DATABASE_URL:
        try:
            db_cfg = _postgres_from_url(DATABASE_URL)
        except Exception:
            # If a malformed DATABASE_URL is set, attempt to use POSTGRES_* variables before failing
            db_cfg = _build_postgres_from_parts()
    else:
        db_cfg = _build_postgres_from_parts()
    DATABASES['default'] = _apply_common_db_options(db_cfg)
except Exception as exc:
    # Never fall back to SQLite; always fail fast with clear guidance
    raise RuntimeError(
        (
            "Failed to configure PostgreSQL database. Set a valid DATABASE_URL (e.g. postgresql://user:pass@host:5432/db) "
            "or provide POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, and optionally POSTGRES_HOST/POSTGRES_PORT.\n"
            f"Root cause: {exc}"
        )
    ) from exc


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add middleware for serving static files with whitenoise
if IS_PRODUCTION:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
