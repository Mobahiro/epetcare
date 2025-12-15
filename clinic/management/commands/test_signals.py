from django.core.management.base import BaseCommand
from clinic.models import Pet, Owner, Prescription, MedicalRecord, Notification
from datetime import date


class Command(BaseCommand):
    help = 'Test notification signals by creating test data'

    def handle(self, *args, **options):
        # Get first pet and owner
        pet = Pet.objects.first()
        if not pet:
            self.stdout.write(self.style.ERROR('No pets found in database'))
            return
        
        owner = pet.owner
        self.stdout.write(self.style.SUCCESS(f'Using pet: {pet.name} (owner: {owner.full_name})'))
        
        # Count notifications before
        notif_count_before = Notification.objects.filter(owner=owner).count()
        self.stdout.write(f'Notifications before: {notif_count_before}')
        
        # Create a prescription
        self.stdout.write('\nCreating prescription...')
        prescription = Prescription.objects.create(
            pet=pet,
            medication_name='Test Medication',
            dosage='1 tablet daily',
            instructions='Take with food',
            date_prescribed=date.today(),
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'Created prescription: {prescription.id}'))
        
        # Create a medical record
        self.stdout.write('\nCreating medical record...')
        record = MedicalRecord.objects.create(
            pet=pet,
            visit_date=date.today(),
            condition='Test Condition',
            treatment='Test Treatment',
            vet_notes='Test notes'
        )
        self.stdout.write(self.style.SUCCESS(f'Created medical record: {record.id}'))
        
        # Count notifications after
        notif_count_after = Notification.objects.filter(owner=owner).count()
        self.stdout.write(f'\nNotifications after: {notif_count_after}')
        self.stdout.write(f'New notifications created: {notif_count_after - notif_count_before}')
        
        # List recent notifications
        recent_notifs = Notification.objects.filter(owner=owner).order_by('-created_at')[:5]
        self.stdout.write('\nRecent notifications:')
        for notif in recent_notifs:
            self.stdout.write(f'  - [{notif.id}] {notif.title}: {notif.message[:50]}...')
