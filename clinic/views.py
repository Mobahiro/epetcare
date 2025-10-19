from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MedicalRecord, Owner, Pet, Appointment, Notification
from .forms import OwnerForm, PetForm, PetCreateForm, AppointmentForm, RegisterForm, UserProfileForm


def home(request):
    return render(request, 'clinic/home.html')


def about_us(request):
    return render(request, 'clinic/about_us.html')


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
    notifications = Notification.objects.filter(owner=owner).order_by('-created_at')[:8] if owner else []
    unread_count = Notification.objects.filter(owner=owner, is_read=False).count() if owner else 0
    # Show a subtle toast for the latest unread notification (one-time per load)
    if owner and unread_count:
        latest_unread = Notification.objects.filter(owner=owner, is_read=False).order_by('-created_at').first()
        if latest_unread:
            messages.info(request, f"🔔 {latest_unread.title}: {latest_unread.message[:120]}" + ("…" if len(latest_unread.message) > 120 else ""))
    return render(request, 'clinic/dashboard.html', {
        "owner": owner,
        "pets": pets,
        "appointments": upcoming,
        "notifications": notifications,
        "unread_count": unread_count,
    })


@login_required
def notifications_list(request):
    owner = getattr(request.user, 'owner_profile', None)
    items = Notification.objects.filter(owner=owner).order_by('-created_at') if owner else []
    return render(request, 'clinic/notifications.html', {"notifications": items})


@login_required
def notification_mark_read(request, pk: int):
    owner = getattr(request.user, 'owner_profile', None)
    try:
        notif = Notification.objects.get(pk=pk, owner=owner)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        messages.success(request, "Notification marked as read.")
    except Notification.DoesNotExist:
        messages.error(request, "Notification not found.")
    return redirect(request.GET.get('next') or 'dashboard')


@login_required
def notifications_mark_all_read(request):
    owner = getattr(request.user, 'owner_profile', None)
    Notification.objects.filter(owner=owner, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect(request.GET.get('next') or 'dashboard')


@login_required
def edit_profile(request):
    owner = getattr(request.user, 'owner_profile', None)
    if not owner:
        messages.error(request, "Owner profile not found for your account.")
        return redirect('dashboard')

    if request.method == 'POST':
        # Process both forms
        user_form = UserProfileForm(request.POST, instance=request.user)
        owner_form = OwnerForm(request.POST, instance=owner)

        if user_form.is_valid() and owner_form.is_valid():
            user_form.save()
            owner_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        owner_form = OwnerForm(instance=owner)

    return render(request, 'clinic/profile.html', {
        'user_form': user_form,
        'owner_form': owner_form,
        'owner': owner
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'clinic/change_password.html', {'form': form})


# Owners

@login_required
def owner_list(request):
    owner = getattr(request.user, 'owner_profile', None)
    # Only show the current user's owner profile to avoid cross-account access
    owners = Owner.objects.filter(pk=owner.pk) if owner else Owner.objects.none()
    return render(request, 'clinic/owner_list.html', {"owners": owners})


@login_required
def owner_create(request):
    # Typically owners are created at registration; prevent creating extra owners
    existing = getattr(request.user, 'owner_profile', None)
    if existing:
        messages.info(request, "Owner profile already exists.")
        return redirect('owner_detail', pk=existing.pk)
    if request.method == 'POST':
        form = OwnerForm(request.POST)
        if form.is_valid():
            owner = form.save(commit=False)
            owner.user = request.user
            owner.save()
            return redirect('owner_detail', pk=owner.pk)
    else:
        form = OwnerForm()
    return render(request, 'clinic/owner_form.html', {"form": form})


@login_required
def owner_detail(request, pk: int):
    # Only allow access to the logged-in user's owner profile
    current_owner = getattr(request.user, 'owner_profile', None)
    if not current_owner:
        messages.error(request, "Owner profile not found for your account.")
        return redirect('dashboard')
    owner = get_object_or_404(Owner, pk=pk)
    if owner.pk != current_owner.pk:
        messages.error(request, "Not authorized to view this owner.")
        return redirect('dashboard')
    pets = owner.pets.all().order_by('name')
    return render(request, 'clinic/owner_detail.html', {"owner": owner, "pets": pets})


# Pets

@login_required
def pet_list(request):
    owner = getattr(request.user, 'owner_profile', None)
    pets = Pet.objects.select_related('owner').filter(owner=owner).order_by('name') if owner else Pet.objects.none()
    return render(request, 'clinic/pet_list.html', {"pets": pets})


@login_required
def pet_create(request):
    owner = getattr(request.user, 'owner_profile', None)
    if not owner:
        messages.error(request, "Owner profile not found for your account.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = PetCreateForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = owner
            pet.save()
            messages.success(request, f"Pet {pet.name} has been successfully added.")
            return redirect('pet_detail', pk=pet.pk)
    else:
        form = PetCreateForm()
    return render(request, 'clinic/pet_form.html', {"form": form})


@login_required
def pet_detail(request, pk: int):
    owner = getattr(request.user, 'owner_profile', None)
    pet = get_object_or_404(Pet, pk=pk, owner=owner)
    appointments = pet.appointments.all().order_by('-date_time')
    prescriptions = pet.prescriptions.all().order_by('-date_prescribed')
    medical_records = MedicalRecord.objects.filter(pet=pet).order_by('-visit_date')

    return render(request, 'clinic/pet_detail.html', {
        "pet": pet,
        "appointments": appointments,
        "prescriptions": prescriptions,
        "medical_records": medical_records,
    })


@login_required
def pet_edit(request, pk: int):
    owner = getattr(request.user, 'owner_profile', None)
    pet = get_object_or_404(Pet, pk=pk, owner=owner)

    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, f"{pet.name}'s information has been updated successfully.")
            return redirect('pet_detail', pk=pet.pk)
    else:
        form = PetForm(instance=pet)

    return render(request, 'clinic/pet_edit.html', {
        "form": form,
        "pet": pet
    })


@login_required
def pet_delete(request, pk: int):
    owner = getattr(request.user, 'owner_profile', None)
    pet = get_object_or_404(Pet, pk=pk, owner=owner)

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

@login_required
def appointment_list(request):
    owner = getattr(request.user, 'owner_profile', None)
    appointments = Appointment.objects.select_related('pet').filter(pet__owner=owner).order_by('-date_time') if owner else Appointment.objects.none()
    return render(request, 'clinic/appointment_list.html', {"appointments": appointments})


@login_required
def appointment_create(request):
    owner = getattr(request.user, 'owner_profile', None)
    if not owner:
        messages.error(request, "Owner profile not found for your account.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        # Limit pet choices to current owner's pets even on POST
        form.fields['pet'].queryset = Pet.objects.filter(owner=owner)
        if form.is_valid():
            appt = form.save(commit=False)
            # Safety: ensure selected pet belongs to current owner
            if appt.pet.owner_id != owner.id:
                messages.error(request, "Invalid pet selection.")
            else:
                appt.save()
                return redirect('appointment_list')
    else:
        form = AppointmentForm()
        # Limit pet choices to current owner's pets
        form.fields['pet'].queryset = Pet.objects.filter(owner=owner)
    return render(request, 'clinic/appointment_form.html', {"form": form})