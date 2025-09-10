from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import Veterinarian, VetNotification
from .forms import VetRegisterForm
from clinic.models import Owner, Pet, Appointment


def home(request):
    """Veterinarian portal home page"""
    return render(request, 'vet/home.html')


def register(request):
    """Register a new veterinarian"""
    if request.method == 'POST':
        form = VetRegisterForm(request.POST)
        if form.is_valid():
            try:
                user, vet = form.create_user_and_vet()
                login(request, user)
                messages.success(request, "Registration successful! Welcome to ePetCare Veterinarian Portal.")
                return redirect('vet:dashboard')
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
    else:
        form = VetRegisterForm()
    return render(request, 'vet/register.html', {"form": form})


def logout_view(request):
    """Log out a veterinarian"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('vet:home')


@login_required
def dashboard(request):
    """Veterinarian dashboard with patient stats and recent appointments"""
    vet = getattr(request.user, 'vet_profile', None)
    
    # Get counts for dashboard stats
    total_owners = Owner.objects.count()
    total_pets = Pet.objects.count()
    upcoming_appointments = Appointment.objects.filter(
        status='scheduled'
    ).order_by('date_time')[:10]
    
    # Get recent notifications
    notifications = VetNotification.objects.filter(
        veterinarian=vet, 
        is_read=False
    )[:5] if vet else []
    
    context = {
        "vet": vet,
        "total_owners": total_owners,
        "total_pets": total_pets,
        "upcoming_appointments": upcoming_appointments,
        "notifications": notifications,
    }
    
    return render(request, 'vet/dashboard.html', context)


@login_required
def patients(request):
    """List all patients (pets) with their owners"""
    pets = Pet.objects.select_related('owner').order_by('owner__full_name', 'name')
    return render(request, 'vet/patients.html', {"pets": pets})


@login_required
def appointments(request):
    """List all appointments"""
    appointments = Appointment.objects.select_related('pet', 'pet__owner').order_by('-date_time')
    return render(request, 'vet/appointments.html', {"appointments": appointments})


@login_required
def notifications(request):
    """List all notifications for the current veterinarian"""
    vet = getattr(request.user, 'vet_profile', None)
    notifications = VetNotification.objects.filter(veterinarian=vet) if vet else []
    
    # Mark all as read
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('vet:notifications')
        
    return render(request, 'vet/notifications.html', {"notifications": notifications})


@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    vet = getattr(request.user, 'vet_profile', None)
    if vet:
        try:
            notification = VetNotification.objects.get(id=notification_id, veterinarian=vet)
            notification.is_read = True
            notification.save()
            messages.success(request, "Notification marked as read.")
        except VetNotification.DoesNotExist:
            messages.error(request, "Notification not found.")
    
    return redirect('vet:notifications')