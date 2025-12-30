"""
Notification views for vet portal
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from vet.models import VetNotification
from ..mixins import is_veterinarian


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    notification = get_object_or_404(
        VetNotification,
        id=notification_id,
        veterinarian=request.user.vet_profile
    )
    notification.is_read = True
    notification.save()
    
    messages.success(request, "Notification marked as read.")
    return redirect('vet_portal:dashboard')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    count = VetNotification.objects.filter(
        veterinarian=request.user.vet_profile,
        is_read=False
    ).update(is_read=True)
    
    messages.success(request, f"Marked {count} notifications as read.")
    return redirect('vet_portal:dashboard')
