from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from clinic.models import Pet, MedicalRecord
from ..forms import MedicalRecordForm
from ..mixins import vet_required


def _get_vet_branch(request):
    """Get the current vet's branch"""
    return request.user.vet_profile.branch


@login_required
@vet_required
def medical_record_create(request, pet_id):
    vet_branch = _get_vet_branch(request)
    # Only allow access to pets in the vet's branch
    pet = get_object_or_404(Pet.objects.filter(owner__branch=vet_branch), id=pet_id)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            import logging
            logger = logging.getLogger('clinic')
            logger.info(f'[VET_PORTAL] About to save medical record for pet: {pet.name} (id={pet.id})')
            record = form.save(commit=False)
            record.pet = pet  # enforce correct pet
            logger.info(f'[VET_PORTAL] Calling record.save() - this should trigger signal')
            record.save()
            logger.info(f'[VET_PORTAL] Medical record saved with id={record.id}')
            messages.success(request, 'Medical record created successfully.')
            return redirect('vet_portal:patient_detail', pk=pet.id)
    else:
        form = MedicalRecordForm(initial={'pet': pet})
        # Hide pet field in the form when context already sets it
        if 'pet' in form.fields:
            form.fields['pet'].widget = form.fields['pet'].hidden_widget()
    return render(request, 'vet_portal/records/form.html', {
        'form': form,
        'pet': pet,
        'mode': 'create',
        'title': 'Add Medical Record'
    })


@login_required
@vet_required
def medical_record_update(request, pk):
    vet_branch = _get_vet_branch(request)
    # Only allow access to records of pets in the vet's branch
    record = get_object_or_404(
        MedicalRecord.objects.filter(pet__owner__branch=vet_branch),
        pk=pk
    )
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.pet = record.pet  # prevent pet reassignment via form tampering
            obj.save()
            messages.success(request, 'Medical record updated successfully.')
            return redirect('vet_portal:patient_detail', pk=record.pet.id)
    else:
        form = MedicalRecordForm(instance=record)
        # Hide pet field when editing; pet should not be changed here
        if 'pet' in form.fields:
            form.fields['pet'].widget = form.fields['pet'].hidden_widget()
    return render(request, 'vet_portal/records/form.html', {
        'form': form,
        'pet': record.pet,
        'mode': 'edit',
        'title': 'Edit Medical Record'
    })


@login_required
@vet_required
def medical_record_delete(request, pk):
    vet_branch = _get_vet_branch(request)
    # Only allow access to records of pets in the vet's branch
    record = get_object_or_404(
        MedicalRecord.objects.filter(pet__owner__branch=vet_branch),
        pk=pk
    )
    
    pet_id = record.pet.id
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Medical record deleted.')
        return redirect('vet_portal:patient_detail', pk=pet_id)
    return render(request, 'vet_portal/records/confirm_delete.html', {'record': record})


@login_required
@vet_required
def medical_record_detail(request, pk):
    """Display detailed view of a medical record - only for vet's branch"""
    vet_branch = _get_vet_branch(request)
    record = get_object_or_404(
        MedicalRecord.objects.select_related('pet', 'pet__owner').filter(
            pet__owner__branch=vet_branch
        ),
        pk=pk
    )
    
    context = {
        'record': record,
        'pet': record.pet,
    }
    return render(request, 'vet_portal/records/detail.html', context)


@login_required
@vet_required
def medical_record_list(request):
    """List all medical records - only for vet's branch"""
    vet_branch = _get_vet_branch(request)
    records = MedicalRecord.objects.filter(
        pet__owner__branch=vet_branch
    ).select_related(
        'pet', 'pet__owner'
    ).order_by('-visit_date')
    
    context = {
        'records': records,
    }
    return render(request, 'vet_portal/records/list.html', context)
