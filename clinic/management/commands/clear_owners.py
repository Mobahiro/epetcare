from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinic.models import Owner, Pet, Appointment, Notification, MedicalRecord, Prescription
from django.db import transaction


class Command(BaseCommand):
    help = 'Clear all pet owner data (owners, pets, appointments, notifications, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all owner data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                '\nThis will DELETE ALL pet owner data including:\n'
                '  - All Owner accounts\n'
                '  - All Pets\n'
                '  - All Appointments\n'
                '  - All Medical Records\n'
                '  - All Prescriptions\n'
                '  - All Notifications\n'
                '  - All associated User accounts\n\n'
                'To confirm, run: python manage.py clear_owners --confirm'
            ))
            return

        with transaction.atomic():
            # Count before deletion
            owner_count = Owner.objects.count()
            pet_count = Pet.objects.count()
            appointment_count = Appointment.objects.count()
            record_count = MedicalRecord.objects.count()
            prescription_count = Prescription.objects.count()
            notification_count = Notification.objects.count()
            
            self.stdout.write(f'\nDeleting:')
            self.stdout.write(f'  {owner_count} Owners')
            self.stdout.write(f'  {pet_count} Pets')
            self.stdout.write(f'  {appointment_count} Appointments')
            self.stdout.write(f'  {record_count} Medical Records')
            self.stdout.write(f'  {prescription_count} Prescriptions')
            self.stdout.write(f'  {notification_count} Notifications')
            
            # Get user IDs associated with owners
            owner_user_ids = list(Owner.objects.values_list('user_id', flat=True))
            
            # Delete in correct order (foreign key dependencies)
            Notification.objects.all().delete()
            Prescription.objects.all().delete()
            MedicalRecord.objects.all().delete()
            Appointment.objects.all().delete()
            Pet.objects.all().delete()
            Owner.objects.all().delete()
            
            # Delete associated user accounts
            deleted_users = User.objects.filter(id__in=owner_user_ids).delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully deleted all pet owner data and {deleted_users[0]} user accounts!'
            ))
