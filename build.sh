#!/usr/bin/env bash
set -euo pipefail

# Install server dependencies
pip install -r requirements.txt

# Create media directory if it doesn't exist
mkdir -p media/pet_images

# Set proper permissions
chmod -R 755 media

# Collect static files for WhiteNoise (prod settings)
python manage.py collectstatic --noinput --settings=config.settings.prod
