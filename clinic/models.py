from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import os


class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile', null=True, blank=True)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.full_name


class Pet(models.Model):
    class Species(models.TextChoices):
        DOG = 'dog', 'Dog'
        CAT = 'cat', 'Cat'
        BIRD = 'bird', 'Bird'
        RABBIT = 'rabbit', 'Rabbit'
        OTHER = 'other', 'Other'

    class Sex(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        UNKNOWN = 'unknown', 'Unknown'

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=80)
    species = models.CharField(max_length=20, choices=Species.choices, default=Species.DOG)
    breed = models.CharField(max_length=80, blank=True)
    sex = models.CharField(max_length=20, choices=Sex.choices, default=Sex.UNKNOWN)
    birth_date = models.DateField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='pet_images/', null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.get_species_display()})"

    @property
    def image_url(self):
        """Return a normalized URL for the image suitable for templates.

        Some older rows may contain values like "media/pet_images/..." which can
        lead to duplicated paths (e.g., "/media/media/...") once MEDIA_URL is
        prefixed. This method normalizes those cases.
        """
        from django.conf import settings

        if not self.image:
            return None

        if hasattr(self.image, 'url'):
            try:
                url = self.image.url

                # Handle empty string
                if not url:
                    return None

                # Clean up any duplicate media paths
                if url.startswith('/media/media/'):
                    url = url.replace('/media/media/', '/media/', 1)

                # Make sure URL has a leading slash
                if url.startswith('media/'):
                    url = '/' + url
                    if url.startswith('/media/media/'):
                        url = url.replace('/media/media/', '/media/', 1)

                # Ensure URL starts with MEDIA_URL
                if not url.startswith('/media/') and not url.startswith(settings.MEDIA_URL):
                    if self.image.name:
                        # Construct URL from image name
                        url = f"{settings.MEDIA_URL.rstrip('/')}/{self.image.name.lstrip('/')}"

                return url
            except Exception as e:
                # Log error but don't break the application
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error generating image_url for Pet {self.id}: {e}")
                return None

        # Handle case where image exists but doesn't have url attribute
        if self.image.name:
            from django.conf import settings
            return f"{settings.MEDIA_URL.rstrip('/')}/{self.image.name.lstrip('/')}"

        return None


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    date_time = models.DateTimeField()
    reason = models.CharField(max_length=160)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    def __str__(self) -> str:
        return f"Appt: {self.pet.name} on {self.date_time:%Y-%m-%d %H:%M}"


class Vaccination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=120)
    date_given = models.DateField()
    next_due = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.pet.name} - {self.vaccine_name}"


class MedicalRecord(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='medical_records')
    visit_date = models.DateField()
    condition = models.CharField(max_length=160)
    treatment = models.TextField(blank=True)
    vet_notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.pet.name} - {self.condition} ({self.visit_date:%Y-%m-%d})"


class Prescription(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=120)
    dosage = models.CharField(max_length=120)
    instructions = models.TextField(blank=True)
    date_prescribed = models.DateField()
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.pet.name} - {self.medication_name}"


class Notification(models.Model):
    class Type(models.TextChoices):
        APPOINTMENT_CREATED = 'appointment_created', 'Appointment Created'
        APPOINTMENT_CANCELLED = 'appointment_cancelled', 'Appointment Cancelled'
        APPOINTMENT_UPDATED = 'appointment_updated', 'Appointment Updated'
        GENERAL = 'general', 'General'

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='notifications')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    notif_type = models.CharField(max_length=40, choices=Type.choices, default=Type.GENERAL)
    title = models.CharField(max_length=160)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.get_notif_type_display()} - {self.title}"
