from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


# Branch choices for vet clinic locations
class Branch(models.TextChoices):
    TAGUIG = 'taguig', 'Taguig'
    PASIG = 'pasig', 'Pasig'
    MAKATI = 'makati', 'Makati'


class VetRegistrationOTP(models.Model):
    """Temporary storage for OTP codes during vet registration"""
    email = models.EmailField()
    personal_email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    registration_data = models.JSONField()  # Store all form data
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"OTP for {self.personal_email} - {self.otp_code}"


class Veterinarian(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vet_profile')
    full_name = models.CharField(max_length=120)
    specialization = models.CharField(max_length=120, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    approval_status = models.CharField(
        max_length=20, 
        choices=ApprovalStatus.choices, 
        default=ApprovalStatus.PENDING,
        help_text='Admin must approve vet accounts before they can access the system'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_vets',
        db_constraint=False
    )
    # Secret access code - required for every login
    access_code = models.CharField(
        max_length=20, 
        unique=True,
        null=True,
        blank=True,
        help_text='Unique access code required for login (in addition to password)'
    )
    personal_email = models.EmailField(
        blank=True,
        help_text='Personal email for sending access code and notifications'
    )
    branch = models.CharField(
        max_length=20,
        choices=Branch.choices,
        default=Branch.TAGUIG,
        help_text='Branch location where this veterinarian is registered'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.get_branch_display()})"
    
    @property
    def is_approved(self):
        """Check if vet is approved to access the system"""
        return self.approval_status == self.ApprovalStatus.APPROVED
    
    @classmethod
    def get_branch_vet_counts(cls):
        """Get count of approved vets per branch"""
        from django.db.models import Count
        counts = cls.objects.filter(
            approval_status=cls.ApprovalStatus.APPROVED
        ).values('branch').annotate(count=Count('id'))
        
        # Initialize all branches with 0
        result = {branch.value: 0 for branch in Branch}
        for item in counts:
            result[item['branch']] = item['count']
        return result


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


class Superadmin(models.Model):
    """Separate model for superadmin accounts - distinct from veterinarians"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='superadmin_profile', db_constraint=False)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(help_text='Email for notifications')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Superadmin'
        verbose_name_plural = 'Superadmins'

    def __str__(self):
        return f"{self.full_name} (Superadmin)"
    
    def save(self, *args, **kwargs):
        # Ensure the linked user has is_superuser=True
        if self.user:
            self.user.is_superuser = True
            self.user.is_staff = True
            self.user.save()
        super().save(*args, **kwargs)