from django.db import models
from django.contrib.auth.models import User
from clinic.models import Pet, Owner, Appointment, MedicalRecord, Prescription
from vet.models import Veterinarian


class VetPortalSettings(models.Model):
    """Settings for the vet portal"""
    last_sync_time = models.DateTimeField(auto_now=True)
    offline_mode_enabled = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Vet Portal Settings'
        verbose_name_plural = 'Vet Portal Settings'


class VetSchedule(models.Model):
    """Schedule for veterinarians"""
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['veterinarian', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.veterinarian.full_name} - {self.date} ({self.start_time} - {self.end_time})"


class Treatment(models.Model):
    """Treatment procedures offered by the clinic"""
    name = models.CharField(max_length=120)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class TreatmentRecord(models.Model):
    """Record of treatments performed"""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='treatments')
    treatment = models.ForeignKey(Treatment, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(Veterinarian, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.treatment.name} for {self.medical_record.pet.name}"


class OfflineChange(models.Model):
    """Tracks changes made while offline for later synchronization"""
    CHANGE_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]
    
    MODEL_TYPES = [
        ('appointment', 'Appointment'),
        ('medical_record', 'Medical Record'),
        ('prescription', 'Prescription'),
        ('treatment_record', 'Treatment Record'),
    ]
    
    change_type = models.CharField(max_length=10, choices=CHANGE_TYPES)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    model_id = models.IntegerField(null=True, blank=True)  # Only for updates/deletes
    data_json = models.TextField()  # JSON serialized data
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_change_type_display()} {self.get_model_type_display()} at {self.created_at}"