#!/usr/bin/env bash
set -euo pipefail

# Install server dependencies
pip install -r requirements.txt

# Create directories
mkdir -p media/pet_images
mkdir -p staticfiles

# Set proper permissions
chmod -R 755 media

# Collect static files for WhiteNoise (prod settings)
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings.prod
echo "Static files collected to staticfiles/"
ls -la staticfiles/ | head -20
