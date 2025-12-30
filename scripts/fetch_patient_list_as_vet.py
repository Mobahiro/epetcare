import os, sys, django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
from vet.models import Veterinarian

c = Client()
user = User.objects.get(username__iexact='kiyo')
# Force login as vet user
c.force_login(user)
resp = c.get('/vet_portal/patients/')
print('STATUS', resp.status_code)
content = resp.content.decode('utf-8')
# Check for pet names present
from clinic.models import Pet
pets = Pet.objects.all()
print('DB PET COUNT', pets.count())
for p in pets:
    found = p.name in content
    print(p.id, p.name, 'FOUND_IN_HTML' if found else 'NOT_FOUND')

# Save HTML dump for inspection
open('tmp_patient_list.html', 'w', encoding='utf-8').write(content)
print('WROTE tmp_patient_list.html')
