#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Optional: Create a superuser if it doesn't exist (useful for initial setup)
# Only uncomment this if you absolutely need an admin user on first deploy and
# understand the security implications. Change password immediately!
# if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
#   echo "Creating superuser..."
#   python manage.py createsuperuser --noinput || true
# fi