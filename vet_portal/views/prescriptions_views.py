from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from clinic.models import Pet, Prescription
from ..forms import PrescriptionForm
from ..mixins import vet_required


def _get_vet_branch(request):
    """Get the current vet's branch"""
    return request.user.vet_profile.branch


@login_required
@vet_required
def prescription_list(request):
    """List all active prescriptions - only for vet's branch"""
    vet_branch = _get_vet_branch(request)
    prescriptions = Prescription.objects.filter(
        pet__owner__branch=vet_branch,
        is_active=True
    ).select_related(
        'pet', 'pet__owner'
    ).order_by('-date_prescribed')
    
    return render(request, 'vet_portal/prescriptions/list.html', {
        'prescriptions': prescriptions,
    })


@login_required
@vet_required
def prescription_create(request, pet_id):
    vet_branch = _get_vet_branch(request)
    # Only allow access to pets in the vet's branch
    pet = get_object_or_404(Pet.objects.filter(owner__branch=vet_branch), id=pet_id)
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            import logging
            from datetime import date
            logger = logging.getLogger('clinic')
            logger.info(f'[VET_PORTAL] About to save prescription for pet: {pet.name} (id={pet.id})')
            rx = form.save(commit=False)
            rx.pet = pet  # enforce correct pet
            rx.date_prescribed = date.today()  # Auto-set to today
            rx.is_active = True  # Auto-set to active
            logger.info(f'[VET_PORTAL] Calling rx.save() - this should trigger signal')
            rx.save()
            logger.info(f'[VET_PORTAL] Prescription saved with id={rx.id}')
            messages.success(request, 'Prescription created successfully.')
            return redirect('vet_portal:patient_detail', pk=pet.id)
    else:
        form = PrescriptionForm(initial={'pet': pet})
        # Hide pet field in the form when context already sets it
        if 'pet' in form.fields:
            form.fields['pet'].widget = form.fields['pet'].hidden_widget()
    return render(request, 'vet_portal/prescriptions/form.html', {
        'form': form,
        'pet': pet,
        'mode': 'create',
        'title': 'Add Prescription'
    })


@login_required
@vet_required
def prescription_update(request, pk):
    vet_branch = _get_vet_branch(request)
    # Only allow access to prescriptions of pets in the vet's branch
    rx = get_object_or_404(
        Prescription.objects.filter(pet__owner__branch=vet_branch),
        pk=pk
    )
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=rx)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.pet = rx.pet  # prevent pet reassignment via form tampering
            obj.save()
            messages.success(request, 'Prescription updated successfully.')
            return redirect('vet_portal:patient_detail', pk=rx.pet.id)
    else:
        form = PrescriptionForm(instance=rx)
        # Hide pet field when editing; pet should not be changed here
        if 'pet' in form.fields:
            form.fields['pet'].widget = form.fields['pet'].hidden_widget()
    return render(request, 'vet_portal/prescriptions/form.html', {
        'form': form,
        'pet': rx.pet,
        'mode': 'edit',
        'title': 'Edit Prescription'
    })


@login_required
@vet_required
def prescription_delete(request, pk):
    vet_branch = _get_vet_branch(request)
    # Only allow access to prescriptions of pets in the vet's branch
    rx = get_object_or_404(
        Prescription.objects.filter(pet__owner__branch=vet_branch),
        pk=pk
    )
    
    pet_id = rx.pet.id
    if request.method == 'POST':
        rx.delete()
        messages.success(request, 'Prescription deleted.')
        return redirect('vet_portal:patient_detail', pk=pet_id)
    return render(request, 'vet_portal/prescriptions/confirm_delete.html', {'prescription': rx})
