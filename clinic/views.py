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
    import logging
    logger = logging.getLogger(__name__)

    owner = getattr(request.user, 'owner_profile', None)
    if not owner:
        messages.error(request, "Owner profile not found for your account.")
        return redirect('dashboard')

    # Log environment information for debugging
    from django.conf import settings
    logger.info(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    logger.info(f"MEDIA_URL: {settings.MEDIA_URL}")
    import os
    logger.info(f"MEDIA_ROOT exists: {os.path.exists(settings.MEDIA_ROOT)}")
    logger.info(f"MEDIA_ROOT permissions: {oct(os.stat(settings.MEDIA_ROOT).st_mode & 0o777)}")
    pet_images_dir = os.path.join(settings.MEDIA_ROOT, 'pet_images')
    if not os.path.exists(pet_images_dir):
        try:
            os.makedirs(pet_images_dir, exist_ok=True)
            logger.info(f"Created pet_images directory: {pet_images_dir}")
        except Exception as e:
            logger.error(f"Failed to create pet_images directory: {e}")
    else:
        logger.info(f"pet_images directory exists: {pet_images_dir}")
        logger.info(f"pet_images permissions: {oct(os.stat(pet_images_dir).st_mode & 0o777)}")

    if request.method == 'POST':
        logger.info("Processing POST request for pet creation")
        logger.info(f"Files in request: {request.FILES}")
        logger.info(f"POST data: {request.POST}")

        # Create a clean form instance
        form = PetCreateForm(request.POST, request.FILES)

        if form.is_valid():
            logger.info("Form is valid, proceeding with pet creation")
            try:
                # Create the pet object but don't save to DB yet
                pet = form.save(commit=False)
                pet.owner = owner

                # Handle image upload - first save pet without image
                has_image = False
                if 'image' in request.FILES:
                    image_file = request.FILES['image']
                    has_image = True
                    logger.info(f"Image upload detected: name={image_file.name}, size={image_file.size}, content_type={image_file.content_type}")

                # Save pet first without image
                if has_image:
                    # Temporarily remove image to save pet first
                    temp_image = image_file
                    form.cleaned_data['image'] = None
                    pet.image = None

                # Initial save
                logger.info("Saving pet without image first")
                pet.save()
                logger.info(f"Pet saved with ID: {pet.id}")

                # Now handle the image if present
                if has_image:
                    try:
                        # Check/create directory
                        os.makedirs(pet_images_dir, exist_ok=True)
                        logger.info("Verified pet_images directory exists")

                        # Create a unique filename
                        import uuid
                        file_extension = os.path.splitext(temp_image.name)[1].lower()
                        unique_filename = f"pet_{pet.id}_{uuid.uuid4().hex[:8]}{file_extension}"
                        image_path = os.path.join('pet_images', unique_filename)

                        # Save the file manually
                        full_path = os.path.join(settings.MEDIA_ROOT, 'pet_images', unique_filename)
                        logger.info(f"Saving image to: {full_path}")

                        with open(full_path, 'wb+') as destination:
                            for chunk in temp_image.chunks():
                                destination.write(chunk)

                        logger.info(f"Image saved successfully at {full_path}")

                        # Update the pet with the image path
                        pet.image = image_path
                        pet.save(update_fields=['image'])
                        logger.info(f"Pet updated with image path: {pet.image}")

                    except Exception as img_error:
                        import traceback
                        logger.error(f"Error saving image: {img_error}\n{traceback.format_exc()}")
                        # Continue with pet creation even if image fails

                messages.success(request, f"Pet {pet.name} has been successfully added.")

                if pet.image:
                    image_url = pet.image_url or f"/media/{pet.image}"
                    messages.info(request, f"Pet image saved at: {image_url}")

                return redirect('pet_detail', pk=pet.pk)

            except Exception as e:
                import traceback
                error_msg = str(e)
                error_details = traceback.format_exc()
                logger.error(f"Error saving pet: {error_msg}\n{error_details}")
                messages.error(request, f"Error saving pet: {error_msg}")
        else:
            logger.error(f"Pet form validation errors: {form.errors}")
            messages.error(request, f"There were errors in your form. Please check and try again.")
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