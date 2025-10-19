from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from clinic.models import Pet, Prescription
from ..forms import PrescriptionForm
from ..mixins import vet_required


@login_required
@vet_required
def prescription_create(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            rx = form.save(commit=False)
            rx.pet = pet  # enforce correct pet
            rx.save()
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
    rx = get_object_or_404(Prescription, pk=pk)
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
    rx = get_object_or_404(Prescription, pk=pk)
    pet_id = rx.pet.id
    if request.method == 'POST':
        rx.delete()
        messages.success(request, 'Prescription deleted.')
        return redirect('vet_portal:patient_detail', pk=pet_id)
    return render(request, 'vet_portal/prescriptions/confirm_delete.html', {'prescription': rx})
