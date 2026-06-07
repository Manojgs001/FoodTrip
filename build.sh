#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Load initial restaurant and menu data (only if no restaurants exist)
python manage.py shell -c "
from delivery.models import Restaurant
if not Restaurant.objects.exists():
    from django.core.management import call_command
    call_command('loaddata', 'delivery/fixtures/initial_data.json')
    print('Fixtures loaded successfully.')
else:
    print('Data already exists, skipping fixture load.')
"
