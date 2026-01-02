"""
Appointment views for vet portal
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from clinic.models import Appointment, Pet
from ..mixins import is_veterinarian


@login_required
def appointment_list(request):
    """List all appointments - filtered by vet's branch"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    # Get the vet's branch
    vet = request.user.vet_profile
    vet_branch = vet.branch
    
    # Auto-update missed appointments (past scheduled → missed)
    Appointment.update_missed_appointments()
    
    # Only show appointments for pets in the vet's branch
    appointments = Appointment.objects.filter(
        pet__owner__branch=vet_branch
    ).select_related(
        'pet', 'pet__owner'
    ).order_by('-date_time')
    
    context = {
        'appointments': appointments,
        'vet_branch': vet.get_branch_display(),
    }
    return render(request, 'vet_portal/appointments/list.html', context)


@login_required
def appointment_detail(request, pk):
    """View appointment details - must be in vet's branch"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    # Get the vet's branch
    vet = request.user.vet_profile
    vet_branch = vet.branch
    
    # Only allow viewing appointments from the vet's branch
    appointment = get_object_or_404(
        Appointment.objects.select_related('pet', 'pet__owner').filter(
            pet__owner__branch=vet_branch
        ), 
        pk=pk
    )
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'vet_portal/appointments/detail.html', context)


@login_required
def appointment_complete(request, pk):
    """Mark an appointment as completed - must be in vet's branch"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    # Get the vet's branch
    vet = request.user.vet_profile
    vet_branch = vet.branch
    
    # Only allow completing appointments from the vet's branch
    appointment = get_object_or_404(
        Appointment.objects.filter(pet__owner__branch=vet_branch),
        pk=pk
    )
    
    if request.method == 'POST':
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, f"Appointment for {appointment.pet.name} marked as completed.")
    
    return redirect('vet_portal:appointment_detail', pk=pk)


@login_required
def appointment_cancel(request, pk):
    """Cancel an appointment - must be in vet's branch"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    # Get the vet's branch
    vet = request.user.vet_profile
    vet_branch = vet.branch
    
    # Only allow cancelling appointments from the vet's branch
    appointment = get_object_or_404(
        Appointment.objects.filter(pet__owner__branch=vet_branch),
        pk=pk
    )
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, f"Appointment for {appointment.pet.name} has been cancelled.")
    
    return redirect('vet_portal:appointment_detail', pk=pk)


@login_required
def appointment_create(request):
    """Create a new appointment (vet portal)"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    # Get the vet's branch to filter pets
    vet = request.user.vet_profile
    vet_branch = vet.branch
    
    # Get pets from the same branch as the vet
    pets = Pet.objects.filter(owner__branch=vet_branch).select_related('owner').order_by('name')
    
    if request.method == 'POST':
        pet_id = request.POST.get('pet')
        date_time_str = request.POST.get('date_time')
        reason = request.POST.get('reason', '')
        notes = request.POST.get('notes', '')
        
        if not pet_id or not date_time_str:
            messages.error(request, "Please select a pet and date/time.")
            return render(request, 'vet_portal/appointments/form.html', {'pets': pets})
        
        try:
            from datetime import datetime, timedelta
            # Parse datetime string
            date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
            date_time = timezone.make_aware(date_time) if timezone.is_naive(date_time) else date_time
            
            pet = get_object_or_404(Pet, pk=pet_id)
            
            # Verify pet belongs to same branch as vet
            if pet.owner.branch != vet_branch:
                messages.error(request, "You can only schedule appointments for pets in your branch.")
                return render(request, 'vet_portal/appointments/form.html', {'pets': pets})
            
            # Check for duplicate appointment times (within 30 minute window)
            time_window = timedelta(minutes=30)
            window_start = date_time - time_window
            window_end = date_time + time_window
            
            conflicting_appointments = Appointment.objects.filter(
                pet__owner__branch=vet_branch,
                date_time__gte=window_start,
                date_time__lte=window_end,
                status='scheduled'
            )
            
            if conflicting_appointments.exists():
                conflict = conflicting_appointments.first()
                messages.error(
                    request,
                    f"This time slot is not available. There is already an appointment scheduled "
                    f"at {conflict.date_time.strftime('%I:%M %p')} for {conflict.pet.name}. "
                    f"Please choose a different time (at least 30 minutes apart)."
                )
                return render(request, 'vet_portal/appointments/form.html', {'pets': pets})
            
            appointment = Appointment.objects.create(
                pet=pet,
                date_time=date_time,
                reason=reason,
                notes=notes,
                status='scheduled'
            )
            messages.success(request, f"Appointment scheduled for {pet.name} on {date_time.strftime('%B %d, %Y at %I:%M %p')}.")
            return redirect('vet_portal:appointment_detail', pk=appointment.pk)
        except Exception as e:
            messages.error(request, f"Error creating appointment: {str(e)}")
    
    context = {
        'pets': pets,
    }
    return render(request, 'vet_portal/appointments/form.html', context)
