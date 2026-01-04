#!/usr/bin/env bash
set -euo pipefail

# Install server dependencies
pip install -r requirements.txt

# Create directories
mkdir -p media/pet_images
mkdir -p staticfiles

# Set proper permissions
chmod -R 755 media

# Debug: Show what apps are installed
echo "=== Debug: Checking static file locations ==="
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()
from django.conf import settings
print('INSTALLED_APPS:', settings.INSTALLED_APPS)
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATICFILES_STORAGE:', settings.STATICFILES_STORAGE)
from django.contrib.staticfiles import finders
print('Static file finders:', [f.__class__.__name__ for f in finders.get_finders()])
"

# Collect static files
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput -v 2 --settings=config.settings.prod

echo "=== Static files collected ==="
ls -la staticfiles/ | head -30
