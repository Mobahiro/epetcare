import os, sys, django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev')
django.setup()
from vet.models import Veterinarian
from django.contrib.auth.models import User
print('VET COUNT', Veterinarian.objects.count())
for v in Veterinarian.objects.all():
    print(v.id, v.full_name, getattr(v.user,'username',None), getattr(v.user,'email',None))
print('\nUSERS with username kiyo:')
for u in User.objects.filter(username__iexact='kiyo'):
    print(u.id, u.username, u.email)
