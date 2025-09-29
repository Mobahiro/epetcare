from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinic.models import Owner, Pet, Appointment, Vaccination, MedicalRecord, Prescription
from vet.models import Veterinarian, VetNotification

class Command(BaseCommand):
    help = "Delete all users and related clinic data (dangerous)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes-i-am-sure",
            dest="yes_i_am_sure",
            action="store_true",
            help="Confirm deletion of ALL users and related data."
        )

    def handle(self, *args, **options):
        if not options.get("yes_i_am_sure"):
            self.stdout.write(self.style.ERROR("Refusing to proceed without --yes-i-am-sure"))
            return

        self.stdout.write("Deleting clinic domain data...")
        Prescription.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Vaccination.objects.all().delete()
        Appointment.objects.all().delete()
        Pet.objects.all().delete()
        Owner.objects.all().delete()
        self.stdout.write("Deleting vet domain data...")
        VetNotification.objects.all().delete()
        Veterinarian.objects.all().delete()

        self.stdout.write("Deleting auth users...")
        # You may want to preserve superusers; for now we delete all
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("All users and related data deleted."))
