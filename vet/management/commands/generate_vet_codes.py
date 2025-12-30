"""
Management command to generate access codes for existing veterinarians
"""
from django.core.management.base import BaseCommand
from vet.models import Veterinarian
import secrets
import string


class Command(BaseCommand):
    help = 'Generate access codes for veterinarians who don\'t have one'

    def generate_access_code(self):
        """Generate a unique 8-character access code"""
        while True:
            # Generate code: 3 letters + 5 digits (e.g., ABC12345)
            letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))
            digits = ''.join(secrets.choice(string.digits) for _ in range(5))
            code = f"{letters}{digits}"
            
            # Ensure it's unique
            if not Veterinarian.objects.filter(access_code=code).exists():
                return code

    def handle(self, *args, **options):
        vets_without_code = Veterinarian.objects.filter(access_code__isnull=True)
        
        count = vets_without_code.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All veterinarians already have access codes.'))
            return
        
        self.stdout.write(f'Found {count} veterinarian(s) without access codes.')
        self.stdout.write('Generating codes...\n')
        
        for vet in vets_without_code:
            code = self.generate_access_code()
            vet.access_code = code
            vet.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {vet.full_name} ({vet.user.username}): {code}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully generated {count} access code(s).'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  Please share these codes with the respective veterinarians securely.'
            )
        )
