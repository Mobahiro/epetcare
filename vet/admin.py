"""
Django admin configuration for Vet app
Includes vet approval management
"""
from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from .models import Veterinarian, VetNotification, VetRegistrationOTP


@admin.action(description='Approve selected veterinarians')
def approve_vets(modeladmin, request, queryset):
    """Bulk action to approve veterinarians"""
    updated = queryset.filter(
        approval_status=Veterinarian.ApprovalStatus.PENDING
    ).update(
        approval_status=Veterinarian.ApprovalStatus.APPROVED,
        approved_at=timezone.now(),
        approved_by=request.user
    )
    
    if updated:
        messages.success(request, f'{updated} veterinarian(s) approved successfully.')
    else:
        messages.warning(request, 'No pending veterinarians were selected.')


@admin.action(description='Reject selected veterinarians')
def reject_vets(modeladmin, request, queryset):
    """Bulk action to reject veterinarians"""
    updated = queryset.update(
        approval_status=Veterinarian.ApprovalStatus.REJECTED
    )
    messages.success(request, f'{updated} veterinarian(s) rejected.')


@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'license_number', 
        'access_code',
        'approval_status', 
        'approved_at',
        'created_at'
    ]
    list_filter = ['approval_status', 'specialization', 'created_at']
    search_fields = ['full_name', 'license_number', 'user__username', 'user__email', 'access_code']
    readonly_fields = ['created_at', 'approved_at', 'approved_by', 'access_code']
    actions = [approve_vets, reject_vets]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'personal_email')
        }),
        ('Professional Details', {
            'fields': ('license_number', 'specialization', 'phone', 'bio')
        }),
        ('Security', {
            'fields': ('access_code',),
            'description': 'Each vet has a unique access code required for login (in addition to password).'
        }),
        ('Approval Status', {
            'fields': ('approval_status', 'approved_at', 'approved_by'),
            'description': 'Veterinarians must be approved before they can access the system.'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # If admin is manually approving, set approval metadata
        if change and 'approval_status' in form.changed_data:
            if obj.approval_status == Veterinarian.ApprovalStatus.APPROVED:
                if not obj.approved_at:
                    obj.approved_at = timezone.now()
                if not obj.approved_by:
                    obj.approved_by = request.user
        
        super().save_model(request, obj, form, change)


@admin.register(VetNotification)
class VetNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'veterinarian', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['title', 'message', 'veterinarian__full_name']
    readonly_fields = ['created_at']


@admin.register(VetRegistrationOTP)
class VetRegistrationOTPAdmin(admin.ModelAdmin):
    list_display = ('personal_email', 'otp_code', 'created_at', 'expires_at', 'is_used', 'is_expired_status')
    list_filter = ('is_used', 'created_at')
    search_fields = ('personal_email', 'email', 'otp_code')
    readonly_fields = ('created_at', 'expires_at', 'registration_data')
    
    def is_expired_status(self, obj):
        return obj.is_expired()
    is_expired_status.boolean = True
    is_expired_status.short_description = 'Expired?'
