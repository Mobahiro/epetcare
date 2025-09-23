from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Owner, Pet, Appointment
from .forms import OwnerForm, PetForm, AppointmentForm, RegisterForm


def home(request):
    return render(request, 'clinic/home.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        print(f"Form valid: {form.is_valid()}")
        if form.is_valid():
            try:
                user, owner = form.create_user_and_owner()
                login(request, user)
                messages.success(request, "Registration successful! Welcome to ePetCare.")
                return redirect('dashboard')
            except Exception as e:
                print(f"Error creating user: {str(e)}")
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = RegisterForm()
    return render(request, 'clinic/register.html', {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


@login_required
def dashboard(request):
    owner = getattr(request.user, 'owner_profile', None)
    pets = Pet.objects.filter(owner=owner).order_by('name') if owner else Pet.objects.none()
    upcoming = Appointment.objects.filter(pet__owner=owner).order_by('date_time')[:10] if owner else Appointment.objects.none()
    return render(request, 'clinic/dashboard.html', {"owner": owner, "pets": pets, "appointments": upcoming})


# Owners

def owner_list(request):
    owners = Owner.objects.order_by('full_name')
    return render(request, 'clinic/owner_list.html', {"owners": owners})


def owner_create(request):
    if request.method == 'POST':
        form = OwnerForm(request.POST)
        if form.is_valid():
            owner = form.save()
            return redirect('owner_detail', pk=owner.pk)
    else:
        form = OwnerForm()
    return render(request, 'clinic/owner_form.html', {"form": form})


def owner_detail(request, pk: int):
    owner = get_object_or_404(Owner, pk=pk)
    pets = owner.pets.all().order_by('name')
    return render(request, 'clinic/owner_detail.html', {"owner": owner, "pets": pets})


# Pets

def pet_list(request):
    pets = Pet.objects.select_related('owner').order_by('name')
    return render(request, 'clinic/pet_list.html', {"pets": pets})


def pet_create(request):
    if request.method == 'POST':
        form = PetForm(request.POST)
        if form.is_valid():
            pet = form.save()
            return redirect('pet_detail', pk=pet.pk)
    else:
        initial = {}
        owner_id = request.GET.get('owner')
        if owner_id:
            initial['owner'] = owner_id
        form = PetForm(initial=initial)
    return render(request, 'clinic/pet_form.html', {"form": form})


def pet_detail(request, pk: int):
    pet = get_object_or_404(Pet, pk=pk)
    appointments = pet.appointments.all().order_by('-date_time')
    vaccinations = pet.vaccinations.all().order_by('-date_given')
    medical_records = MedicalRecord.objects.filter(pet=pet).order_by('-date')
    
    return render(request, 'clinic/pet_detail.html', {
        "pet": pet,
        "appointments": appointments,
        "vaccinations": vaccinations,
        "medical_records": medical_records,
    })


def pet_delete(request, pk: int):
    pet = get_object_or_404(Pet, pk=pk)
    
    # Check if this is a POST request (form submission)
    if request.method == 'POST':
        owner_id = pet.owner.id
        pet_name = pet.name
        pet.delete()
        messages.success(request, f"Pet '{pet_name}' has been deleted successfully.")
        
        # Redirect to owner detail if coming from there, otherwise to pet list
        redirect_to = request.POST.get('next', 'pet_list')
        if redirect_to == 'owner_detail':
            return redirect('owner_detail', pk=owner_id)
        else:
            return redirect('pet_list')
    
    # If GET request, show confirmation page
    return render(request, 'clinic/pet_confirm_delete.html', {"pet": pet})


# Medical Records

def medical_record_delete(request, pk: int):
    record = get_object_or_404(MedicalRecord, pk=pk)
    pet = record.pet
    
    # Check if this is a POST request (form submission)
    if request.method == 'POST':
        record_type = record.record_type
        record.delete()
        messages.success(request, f"Medical record '{record_type}' has been deleted successfully.")
        return redirect('pet_detail', pk=pet.pk)
    
    # If GET request, show confirmation page
    return render(request, 'clinic/medical_record_confirm_delete.html', {"record": record})


# Appointments

def appointment_list(request):
    appointments = Appointment.objects.select_related('pet').order_by('-date_time')
    return render(request, 'clinic/appointment_list.html', {"appointments": appointments})


def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('appointment_list')
    else:
        form = AppointmentForm()
    return render(request, 'clinic/appointment_form.html', {"form": form})