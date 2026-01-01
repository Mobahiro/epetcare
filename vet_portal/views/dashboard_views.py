from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from clinic.models import Appointment, MedicalRecord, Pet, Prescription
from vet.models import VetNotification

from ..mixins import is_veterinarian


@login_required
def dashboard(request):
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied. You need veterinarian privileges.")
        return redirect('home')
    
    # Auto-update missed appointments (past scheduled → missed)
    Appointment.update_missed_appointments()
    
    # Get veterinarian
    vet = request.user.vet_profile
    
    # Get today's appointments
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        date_time__date=today
    ).select_related('pet', 'pet__owner').order_by('date_time')
    
    # Get upcoming appointments (next 7 days)
    upcoming_appointments = Appointment.objects.filter(
        date_time__date__gt=today,
        date_time__date__lte=today + timezone.timedelta(days=7)
    ).select_related('pet', 'pet__owner').order_by('date_time')
    
    # Get recent medical records
    recent_records = MedicalRecord.objects.select_related(
        'pet', 'pet__owner'
    ).order_by('-visit_date')[:10]
    
    # Get unread notifications
    notifications = VetNotification.objects.filter(
        veterinarian=vet, is_read=False
    ).order_by('-created_at')[:5]
    
    # Get unread notification count
    unread_notifications_count = VetNotification.objects.filter(
        veterinarian=vet, is_read=False
    ).count()
    
    # Get statistics
    total_pets = Pet.objects.count()
    total_appointments = Appointment.objects.filter(
        date_time__date__gte=today
    ).count()
    total_pending_prescriptions = Prescription.objects.filter(
        is_active=True
    ).count()
    
    context = {
        'vet': vet,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_records': recent_records,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'total_pets': total_pets,
        'total_appointments': total_appointments,
        'total_pending_prescriptions': total_pending_prescriptions,
    }
    
    return render(request, 'vet_portal/dashboard_new.html', context)


def manifest(request):
    """PWA manifest.json for vet portal"""
    manifest_data = {
        "name": "ePetCare Vet Portal",
        "short_name": "ePetCare Vet",
        "description": "Veterinary management portal for ePetCare",
        "start_url": "/vet-portal/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#007bff",
        "icons": [
            {
                "src": "/static/clinic/images/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/clinic/images/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JsonResponse(manifest_data)