#!/usr/bin/env bash
set -euo pipefail

# Install server dependencies
pip install -r requirements.txt

# Create media directory if it doesn't exist
mkdir -p media/pet_images

# Set proper permissions
chmod -R 755 media

# Clear old static files to avoid conflicts
rm -rf staticfiles/*

# Collect static files for WhiteNoise (prod settings)
# Use --clear to ensure clean collection
python manage.py collectstatic --noinput --clear --settings=config.settings.prod
