from django.db import models
from django.contrib.auth.models import User


class Veterinarian(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vet_profile')
    full_name = models.CharField(max_length=120)
    specialization = models.CharField(max_length=120, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class VetNotification(models.Model):
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"