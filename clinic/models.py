from django.db import models
from django.contrib.auth.models import User


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

    def __str__(self) -> str:
        return f"{self.name} ({self.get_species_display()})"


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
