from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.http import Http404

from clinic.models import Pet, MedicalRecord, Prescription
from .forms import MedicalRecordForm, PrescriptionForm
from .mixins import is_veterinarian, VeterinarianRequiredMixin

# Reuse existing views defined under views/ package
from .views.auth_views import VetLoginView, VetLogoutView
from .views.dashboard_views import dashboard
from .views.patient_views import PatientListView, PatientDetailView


def _require_vet(request):
	if not is_veterinarian(request.user):
		messages.error(request, "Access denied. You need veterinarian privileges.")
		return False
	return True


def _get_vet_branch(request):
	"""Get the current vet's branch"""
	return request.user.vet_profile.branch


def _verify_pet_branch(pet, vet_branch):
	"""Verify that a pet belongs to the vet's branch"""
	if pet.owner.branch != vet_branch:
		raise Http404("Pet not found in your branch")


@login_required
def medical_record_create(request, pet_id):
	if not _require_vet(request):
		return redirect('home')
	
	vet_branch = _get_vet_branch(request)
	# Only allow access to pets in the vet's branch
	pet = get_object_or_404(Pet.objects.filter(owner__branch=vet_branch), id=pet_id)
	
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
def medical_record_update(request, pk):
	if not _require_vet(request):
		return redirect('home')
	
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
def medical_record_delete(request, pk):
	if not _require_vet(request):
		return redirect('home')
	
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
def prescription_create(request, pet_id):
	if not _require_vet(request):
		return redirect('home')
	
	vet_branch = _get_vet_branch(request)
	# Only allow access to pets in the vet's branch
	pet = get_object_or_404(Pet.objects.filter(owner__branch=vet_branch), id=pet_id)
	
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
def prescription_update(request, pk):
	if not _require_vet(request):
		return redirect('home')
	
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
def prescription_delete(request, pk):
	if not _require_vet(request):
		return redirect('home')
	
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
