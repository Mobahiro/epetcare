"""
Schedule views for vet portal
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from clinic.models import Appointment
from ..mixins import is_veterinarian


@login_required
def schedule_list(request):
    """Display weekly schedule of appointments"""
    if not is_veterinarian(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    # Get current week's appointments
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    appointments = Appointment.objects.select_related(
        'pet', 'pet__owner'
    ).filter(
        date_time__date__range=[week_start, week_end]
    ).order_by('date_time')
    
    context = {
        'appointments': appointments,
        'week_start': week_start,
        'week_end': week_end,
    }
    return render(request, 'vet_portal/schedule/list.html', context)
