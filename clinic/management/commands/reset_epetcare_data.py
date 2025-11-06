from django.core.management.base import BaseCommand
from django.db import transaction
from clinic.models import Owner, Pet, Appointment, MedicalRecord, Prescription, Notification

class Command(BaseCommand):
    help = 'Delete all user, pet, appointment, medical record, prescription, and notification data from the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('This will delete ALL user, pet, appointment, medical record, prescription, and notification data!'))
        confirm = input('Type YES to confirm: ')
        if confirm != 'YES':
            self.stdout.write(self.style.ERROR('Aborted. No data was deleted.'))
            return
        with transaction.atomic():
            Notification.objects.all().delete()
            Prescription.objects.all().delete()
            MedicalRecord.objects.all().delete()
            Appointment.objects.all().delete()
            Pet.objects.all().delete()
            Owner.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('All ePetCare user, pet, appointment, medical record, prescription, and notification data has been deleted.'))
