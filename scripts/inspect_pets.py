import os, django, sys

# Ensure project root is on sys.path so Django can import the project's
# settings module (the `config` package). This mirrors how `manage.py`
# runs with the project root on PYTHONPATH.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from clinic.models import Pet

pets = Pet.objects.select_related('owner').all()
print('QSET_COUNT', pets.count())
for p in pets:
    owner_name = p.owner.full_name if getattr(p, 'owner', None) else None
    print(f"{p.id}: {p.name} - owner:{owner_name} (owner_id={p.owner_id})")
