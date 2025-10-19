from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from clinic.models import Pet, MedicalRecord
from ..forms import MedicalRecordForm
from ..mixins import vet_required


@login_required
@vet_required
def medical_record_create(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.pet = pet  # enforce correct pet
            record.save()
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
    record = get_object_or_404(MedicalRecord, pk=pk)
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
    record = get_object_or_404(MedicalRecord, pk=pk)
    pet_id = record.pet.id
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Medical record deleted.')
        return redirect('vet_portal:patient_detail', pk=pet_id)
    return render(request, 'vet_portal/records/confirm_delete.html', {'record': record})
