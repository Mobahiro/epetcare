from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import MedicalRecord, Owner, Pet, Appointment, Notification
from .forms import (
    OwnerForm, PetForm, PetCreateForm, AppointmentForm,
    RegisterForm, UserProfileForm,
    PasswordResetRequestForm, PasswordResetOTPForm, PasswordResetSetNewForm,
)
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import timedelta
import random
from .utils.notifications import process_unsent_notifications


def home(request):
    return render(request, 'clinic/home.html')


def about_us(request):
    return render(request, 'clinic/about_us.html')


def register(request):
    if request.method == 'POST':
        # Check if this is OTP verification step (for vets)
        if 'verify_otp' in request.POST:
            return verify_vet_registration_otp(request)
        
        # Check if this is owner OTP verification step
        if 'verify_owner_otp' in request.POST:
            return verify_owner_registration_otp(request)
        
        # Check if this is branch selection step (final step for owners)
        if 'select_branch' in request.POST:
            return complete_owner_registration(request)
        
        form = RegisterForm(request.POST)
        print(f"Form valid: {form.is_valid()}")
        if form.is_valid():
            try:
                # Check if this is a vet registration
                if form.is_vet_registration():
                    # Generate and send OTP instead of creating account immediately
                    return send_vet_registration_otp(request, form)
                else:
                    # Pet owner registration - send OTP first, don't create account yet
                    return send_owner_registration_otp(request, form)
                    
            except Exception as e:
                print(f"Error creating user: {str(e)}")
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = RegisterForm()
    return render(request, 'clinic/register.html', {"form": form})


def send_vet_registration_otp(request, form):
    """Send OTP to vet's personal email for verification"""
    from vet.models import VetRegistrationOTP
    import random
    import json
    
    # Generate 6-digit OTP
    otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Store registration data and OTP
    registration_data = {
        'username': form.cleaned_data['username'].lower(),
        'email': form.cleaned_data['email'].lower(),
        'personal_email': form.cleaned_data['personal_email'],
        'password': form.cleaned_data['password1'],
        'full_name': form.cleaned_data['full_name'],
        'specialization': form.cleaned_data.get('specialization', ''),
        'license_number': form.cleaned_data.get('license_number', ''),
        'phone': form.cleaned_data.get('phone', ''),
    }
    
    # Delete any existing OTP for this email
    VetRegistrationOTP.objects.filter(personal_email=registration_data['personal_email']).delete()
    
    # Create new OTP record
    otp_record = VetRegistrationOTP.objects.create(
        email=registration_data['email'],
        personal_email=registration_data['personal_email'],
        otp_code=otp_code,
        registration_data=registration_data
    )
    
    # Send OTP via email
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to send OTP to {registration_data['personal_email']}")

        from .utils.emailing import send_mail_http

        subject = 'ePetCare Vet Registration - Verification Code'
        body = f'''Dear {registration_data['full_name']},

Thank you for registering as a veterinarian on ePetCare!

Your verification code is: {otp_code}

This code will expire in 10 minutes. Please enter it on the registration page to complete your registration.

Best regards,
ePetCare Team'''

        send_mail_http(
            subject,
            body,
            [registration_data['personal_email']],
            settings.DEFAULT_FROM_EMAIL,
        )

        logger.info(f"OTP email sent to {registration_data['personal_email']}")

        # Store OTP ID in session for verification
        request.session['vet_otp_id'] = otp_record.id
        request.session['vet_personal_email'] = registration_data['personal_email']

        # Clear any stale messages to prevent cross-flow contamination
        storage = messages.get_messages(request)
        storage.used = True

        return render(request, 'clinic/verify_vet_otp.html', {
            'personal_email': registration_data['personal_email'],
            'otp_sent': True
        })
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending OTP email: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        print(f"Error sending OTP email: {e}")
        print(f"Email config - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}, From: {settings.DEFAULT_FROM_EMAIL}")
        messages.error(request, f"Failed to send verification code: {str(e)}. Please contact support.")
        # Clean up the OTP record since email failed
        otp_record.delete()
        return render(request, 'clinic/register.html', {'form': form})


def verify_vet_registration_otp(request):
    """Verify OTP and create vet account"""
    from vet.models import VetRegistrationOTP, Veterinarian
    from django.contrib.auth.models import User
    from django.db import transaction
    
    otp_entered = request.POST.get('otp_code', '').strip()
    otp_id = request.session.get('vet_otp_id')
    
    if not otp_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')
    
    try:
        otp_record = VetRegistrationOTP.objects.get(id=otp_id, is_used=False)
        
        # Check if OTP is expired
        if otp_record.is_expired():
            messages.error(request, "Verification code expired. Please register again.")
            return redirect('register')
        
        # Verify OTP
        if otp_record.otp_code != otp_entered:
            # Clear any stale messages first
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, "Invalid verification code. Please try again.")
            return render(request, 'clinic/verify_vet_otp.html', {
                'personal_email': otp_record.personal_email,
                'otp_sent': True
            })
        
        # OTP is correct - create vet account
        data = otp_record.registration_data
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            # Generate access code
            import secrets
            import string
            while True:
                letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))
                digits = ''.join(secrets.choice(string.digits) for _ in range(5))
                access_code = f"{letters}{digits}"
                
                if not Veterinarian.objects.filter(access_code=access_code).exists():
                    break
            
            # Create veterinarian profile
            vet = Veterinarian.objects.create(
                user=user,
                full_name=data['full_name'],
                specialization=data.get('specialization', ''),
                license_number=data.get('license_number', ''),
                phone=data.get('phone', ''),
                access_code=access_code,
                personal_email=data['personal_email']
            )
            
            # Mark OTP as used
            otp_record.is_used = True
            otp_record.save()
        
        # Send access code via email
        try:
            from .utils.emailing import send_mail_http
            send_mail_http(
                'ePetCare - Your Veterinarian Access Code',
                f'''Dear Dr. {vet.full_name},

Your ePetCare veterinarian account has been created successfully!

Login Credentials:
Username: {user.username}
Access Code: {access_code}

⚠️ IMPORTANT: Keep this access code secure! You'll need it every time you login along with your password.

Your account is pending admin approval. Once approved, you'll be able to access the vet portal.

Best regards,
ePetCare Team''',
                [vet.personal_email],
                settings.DEFAULT_FROM_EMAIL,
            )
        except Exception as e:
            print(f"Error sending access code email: {str(e)}")
        
        # Clear session
        del request.session['vet_otp_id']
        del request.session['vet_personal_email']
        
        messages.success(
            request,
            f"✅ Registration successful! Your access code has been sent to {vet.personal_email}. "
            "Please check your email for login credentials. Your account is pending admin approval."
        )
        return redirect('unified_login')
        
    except VetRegistrationOTP.DoesNotExist:
        messages.error(request, "Invalid verification session. Please register again.")
        return redirect('register')


def send_owner_registration_otp(request, form):
    """Send OTP to pet owner's email for verification before branch selection"""
    from .models import OwnerRegistrationOTP
    import random
    
    # Generate 6-digit OTP
    otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Store registration data (without branch - that comes later)
    registration_data = {
        'username': form.cleaned_data['username'].lower(),
        'email': form.cleaned_data['email'].lower(),
        'password': form.cleaned_data['password1'],
        'full_name': form.cleaned_data['full_name'],
        'phone': form.cleaned_data.get('phone', ''),
        'address': form.cleaned_data.get('address', ''),
    }
    
    # Delete any existing OTP for this email
    OwnerRegistrationOTP.objects.filter(email=registration_data['email']).delete()
    
    # Create new OTP record
    otp_record = OwnerRegistrationOTP.objects.create(
        email=registration_data['email'],
        otp_code=otp_code,
        registration_data=registration_data
    )
    
    # Send OTP via email
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to send OTP to {registration_data['email']}")

        from .utils.emailing import send_mail_http

        subject = 'ePetCare Registration - Verification Code'
        body = f'''Dear {registration_data['full_name']},

Thank you for registering on ePetCare!

Your verification code is: {otp_code}

This code will expire in 30 minutes. Please enter it on the registration page to continue with your registration.

After verification, you will select your preferred branch location.

Best regards,
ePetCare Team'''

        send_mail_http(
            subject,
            body,
            [registration_data['email']],
            settings.DEFAULT_FROM_EMAIL,
        )

        logger.info(f"OTP email sent to {registration_data['email']}")

        # Store OTP ID in session for verification
        request.session['owner_otp_id'] = otp_record.id
        request.session['owner_email'] = registration_data['email']

        # Clear any stale messages to prevent cross-flow contamination
        storage = messages.get_messages(request)
        storage.used = True

        return render(request, 'clinic/verify_owner_otp.html', {
            'email': registration_data['email'],
            'otp_sent': True
        })
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending OTP email: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        print(f"Error sending OTP email: {e}")
        messages.error(request, f"Failed to send verification code: {str(e)}. Please try again.")
        # Clean up the OTP record since email failed
        otp_record.delete()
        return render(request, 'clinic/register.html', {'form': form})


def verify_owner_registration_otp(request):
    """Verify OTP and show branch selection"""
    from .models import OwnerRegistrationOTP
    from vet.models import Veterinarian
    
    otp_entered = request.POST.get('otp_code', '').strip()
    otp_id = request.session.get('owner_otp_id')
    
    if not otp_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')
    
    try:
        otp_record = OwnerRegistrationOTP.objects.get(id=otp_id, is_used=False)
        
        # Check if OTP is expired
        if otp_record.is_expired():
            messages.error(request, "Verification code expired. Please register again.")
            return redirect('register')
        
        # Verify OTP
        if otp_record.otp_code != otp_entered:
            # Clear any stale messages first, then add only the error
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, "Invalid verification code. Please try again.")
            return render(request, 'clinic/verify_owner_otp.html', {
                'email': otp_record.email,
                'otp_sent': True
            })
        
        # OTP is correct - mark as verified and show branch selection
        otp_record.otp_verified = True
        otp_record.save()
        
        # Get vet counts per branch for display
        branch_vet_counts = {
            'taguig': Veterinarian.objects.filter(branch='taguig', approval_status='approved').count(),
            'pasig': Veterinarian.objects.filter(branch='pasig', approval_status='approved').count(),
            'makati': Veterinarian.objects.filter(branch='makati', approval_status='approved').count(),
        }
        
        return render(request, 'clinic/select_branch.html', {
            'email': otp_record.email,
            'full_name': otp_record.registration_data.get('full_name', ''),
            'branch_vet_counts': branch_vet_counts,
        })
        
    except OwnerRegistrationOTP.DoesNotExist:
        messages.error(request, "Invalid verification session. Please register again.")
        return redirect('register')


def complete_owner_registration(request):
    """Complete owner registration after branch selection"""
    from .models import OwnerRegistrationOTP, Owner
    from django.contrib.auth.models import User
    from django.db import transaction
    
    otp_id = request.session.get('owner_otp_id')
    selected_branch = request.POST.get('branch', '').strip()
    
    if not otp_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')
    
    if not selected_branch or selected_branch not in ['taguig', 'pasig', 'makati']:
        messages.error(request, "Please select a valid branch.")
        return redirect('register')
    
    try:
        otp_record = OwnerRegistrationOTP.objects.get(id=otp_id, is_used=False, otp_verified=True)
        
        # Check if OTP is expired
        if otp_record.is_expired():
            messages.error(request, "Session expired. Please register again.")
            return redirect('register')
        
        data = otp_record.registration_data
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            # Create owner profile with selected branch
            owner = Owner.objects.create(
                user=user,
                full_name=data['full_name'],
                email=data['email'],
                phone=data.get('phone', ''),
                address=data.get('address', ''),
                branch=selected_branch
            )
            
            # Mark OTP as used
            otp_record.is_used = True
            otp_record.save()
        
        # Clear session
        del request.session['owner_otp_id']
        del request.session['owner_email']
        
        # Auto-login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        
        branch_display = {'taguig': 'Taguig', 'pasig': 'Pasig', 'makati': 'Makati'}.get(selected_branch, selected_branch)
        messages.success(
            request,
            f"🎉 Registration successful! Welcome to ePetCare, {owner.full_name}! "
            f"You are registered with the {branch_display} branch."
        )
        return redirect('dashboard')
        
    except OwnerRegistrationOTP.DoesNotExist:
        messages.error(request, "Invalid verification session. Please register again.")
        return redirect('register')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


@login_required
def dashboard(request):
    try:
        owner = getattr(request.user, 'owner_profile', None)
    except Exception as e:
        # If there's an issue retrieving the user, log them out and redirect to login
        logout(request)
        messages.error(request, "Session error. Please log in again.")
        return redirect('login')
    
    # Auto-update missed appointments (past scheduled → missed)
    Appointment.update_missed_appointments()
    
    # Opportunistically process any unsent emails for this owner upon visit
    if owner:
        try:
            process_unsent_notifications(owner, limit=10)
        except Exception:
            pass
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
    if owner:
        try:
            process_unsent_notifications(owner, limit=25)
        except Exception:
            pass
    items = Notification.objects.filter(owner=owner).order_by('-created_at') if owner else []
    return render(request, 'clinic/notifications.html', {"notifications": items})


@login_required
def notification_mark_read(request, pk: int):
    owner = getattr(request.user, 'owner_profile', None)
    if not owner:
        messages.error(request, "Owner profile not found.")
        return redirect('dashboard')

    try:
        notif = Notification.objects.get(pk=pk, owner=owner)
        if not notif.is_read:
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


# OTP-based password reset flow
def password_reset_request_otp(request):
    """Step 1: User submits email or username; send OTP to email if user exists."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            users = list(form.get_users(form.cleaned_data.get('email')))
            # Save hint for UX regardless
            request.session['pr_user_hint'] = form.cleaned_data.get('email')
            if users:
                user = users[0]
                request.session['pr_user_id'] = user.id
                # Generate 6-digit OTP
                code = f"{random.randint(0, 999999):06d}"
                from .models import PasswordResetOTP
                # expire after 10 minutes
                expires = timezone.now() + timedelta(minutes=10)

                # Optional: remove previous unused OTPs for this user to avoid confusion
                PasswordResetOTP.objects.filter(user=user, is_used=False, expires_at__gt=timezone.now()).delete()

                PasswordResetOTP.objects.create(user=user, code=code, expires_at=expires)

                # Send email using template
                subject = f"Your {getattr(settings, 'BRAND_NAME', 'ePetCare')} password reset code"
                ctx = {
                    "code": code,
                    "name": getattr(user, 'first_name', '') or None,
                    "year": timezone.now().year,
                    "BRAND_NAME": getattr(settings, 'BRAND_NAME', 'ePetCare'),
                    "EMAIL_BRAND_LOGO_URL": getattr(settings, 'EMAIL_BRAND_LOGO_URL', ''),
                }
                message = render_to_string('clinic/auth/otp_email.txt', ctx)
                html_message = render_to_string('clinic/auth/otp_email.html', ctx)
                try:
                    from .utils.emailing import send_mail_http
                    success = send_mail_http(subject, message, [user.email], settings.DEFAULT_FROM_EMAIL, html_message=html_message)
                    import logging
                    if success:
                        logging.getLogger('clinic').info(f'Password reset OTP email sent to {user.email}')
                    else:
                        logging.getLogger('clinic').error(f'Password reset email failed via HTTP provider')
                except Exception as e:
                    import logging
                    logging.getLogger('clinic').error(f'Password reset email failed: {e}')

            # Always redirect to verify page to avoid enumeration (template shows the info message)
            return redirect('password_reset_verify')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'clinic/auth/otp_reset_request.html', {"form": form})


def password_reset_verify_otp(request):
    """Step 2: Verify OTP and store a session token to allow password set."""
    if request.method == 'POST':
        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['otp']
            from .models import PasswordResetOTP
            user_id = request.session.get('pr_user_id')
            if not user_id:
                messages.error(request, 'Session expired or invalid. Please request a new code.')
                return redirect('password_reset_request')
            otp_qs = PasswordResetOTP.objects.filter(user_id=user_id, code=code, is_used=False).order_by('-created_at')
            otp = otp_qs.first()
            if not otp:
                messages.error(request, 'Invalid code. Please try again.')
            elif otp.is_expired():
                messages.error(request, 'This code has expired. Please request a new one.')
            else:
                # Mark used and allow next step
                otp.is_used = True
                otp.attempts = otp.attempts + 1
                otp.save(update_fields=['is_used', 'attempts'])
                request.session['pr_user_id'] = otp.user_id
                return redirect('password_reset_set_new')
    else:
        form = PasswordResetOTPForm()
    return render(request, 'clinic/auth/otp_reset_verify.html', {"form": form, "hint": request.session.get('pr_user_hint')})


def password_reset_set_new(request):
    """Step 3: Set a new password for the verified user (session-guarded)."""
    user_id = request.session.get('pr_user_id')
    if not user_id:
        messages.error(request, 'Session expired or invalid. Please request a new code.')
        return redirect('password_reset_request')
    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = PasswordResetSetNewForm(user, request.POST)
        if form.is_valid():
            form.save()
            # cleanup session
            request.session.pop('pr_user_id', None)
            request.session.pop('pr_user_hint', None)
            messages.success(request, 'Your password has been updated. You can now log in.')
            return redirect('login')
    else:
        form = PasswordResetSetNewForm(user)
    return render(request, 'clinic/auth/otp_reset_set_new.html', {"form": form})


@login_required
def edit_profile(request):
    """Edit owner profile with rate limiting for sensitive fields.
    
    Security policy:
    - Username: Can change once per month
    - Email: Can change once per month (requires OTP)
    - Password: Can change once per month (requires OTP)
    - Full Name: Admin-only (contact epetcarewebsystem@gmail.com)
    - Phone/Address: Freely editable
    """
    owner = getattr(request.user, 'owner_profile', None)
    if not owner:
        messages.error(request, "Owner profile not found for your account.")
        return redirect('dashboard')

    # Get rate limit status for display
    can_change_username, next_username_date = owner.can_change_username()
    can_change_email, next_email_date = owner.can_change_email()
    can_change_password, next_password_date = owner.can_change_password()

    if request.method == 'POST':
        # Process forms with owner for rate limit checking
        user_form = UserProfileForm(request.POST, instance=request.user, owner=owner)
        owner_form = OwnerForm(request.POST, instance=owner)

        if user_form.is_valid() and owner_form.is_valid():
            # Track if username or email changed (for rate limit timestamps)
            username_changed = user_form.cleaned_data['username'] != request.user.username
            email_changed = user_form.cleaned_data['email'] != request.user.email
            
            # Save user
            user_instance = user_form.save()
            
            # Update rate limit timestamps if fields were changed
            if username_changed:
                owner.last_username_change = timezone.now()
            if email_changed:
                owner.last_email_change = timezone.now()
                # Sync email to owner profile
                owner.email = user_instance.email
            
            # Save owner contact info (phone, address)
            owner_instance = owner_form.save(commit=False)
            if email_changed:
                owner_instance.email = user_instance.email
            owner_instance.save()
            
            # Save rate limit timestamps
            if username_changed or email_changed:
                owner.save(update_fields=['last_username_change', 'last_email_change', 'email'])

            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=request.user, owner=owner)
        owner_form = OwnerForm(instance=owner)

    # Get last updated date
    last_updated = request.user.date_joined
    if hasattr(request.user, 'last_login') and request.user.last_login:
        last_updated = request.user.last_login

    return render(request, 'clinic/profile.html', {
        'user_form': user_form,
        'owner_form': owner_form,
        'owner': owner,
        'last_updated': last_updated,
        # Rate limit status
        'can_change_username': can_change_username,
        'next_username_date': next_username_date,
        'can_change_email': can_change_email,
        'next_email_date': next_email_date,
        'can_change_password': can_change_password,
        'next_password_date': next_password_date,
    })


@login_required
def profile_update_field(request):
    """AJAX endpoint to update a single profile field.
    
    Handles rate limiting for username/email and freely editable fields.
    Returns JSON response.
    """
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    # Check if AJAX request
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    owner = getattr(request.user, 'owner_profile', None)
    if not owner:
        return JsonResponse({'success': False, 'error': 'Owner profile not found'}, status=404)
    
    field = request.POST.get('field')
    value = request.POST.get('value', '').strip()
    
    allowed_fields = ['username', 'email', 'phone', 'address']
    if field not in allowed_fields:
        return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)
    
    try:
        if field == 'username':
            # Check rate limit
            can_change, next_date = owner.can_change_username()
            if not can_change:
                return JsonResponse({
                    'success': False, 
                    'error': f'Username can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.'
                }, status=403)
            
            # Validate username
            if len(value) < 3:
                return JsonResponse({'success': False, 'error': 'Username must be at least 3 characters'}, status=400)
            
            # Check uniqueness
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(username=value).exclude(pk=request.user.pk).exists():
                return JsonResponse({'success': False, 'error': 'This username is already taken'}, status=400)
            
            # Update username
            old_username = request.user.username
            if value != old_username:
                request.user.username = value
                request.user.save(update_fields=['username'])
                owner.last_username_change = timezone.now()
                owner.save(update_fields=['last_username_change'])
            
            return JsonResponse({'success': True, 'message': 'Username updated successfully!'})
        
        elif field == 'email':
            # Check rate limit
            can_change, next_date = owner.can_change_email()
            if not can_change:
                return JsonResponse({
                    'success': False, 
                    'error': f'Email can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.'
                }, status=403)
            
            # Validate email
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(value)
            except ValidationError:
                return JsonResponse({'success': False, 'error': 'Please enter a valid email address'}, status=400)
            
            # Check uniqueness
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=value).exclude(pk=request.user.pk).exists():
                return JsonResponse({'success': False, 'error': 'This email is already in use'}, status=400)
            
            # Update email
            old_email = request.user.email
            if value != old_email:
                request.user.email = value
                request.user.save(update_fields=['email'])
                owner.email = value
                owner.last_email_change = timezone.now()
                owner.save(update_fields=['email', 'last_email_change'])
            
            return JsonResponse({'success': True, 'message': 'Email updated successfully!'})
        
        elif field == 'phone':
            owner.phone = value if value else None
            owner.save(update_fields=['phone'])
            return JsonResponse({'success': True, 'message': 'Phone number updated successfully!'})
        
        elif field == 'address':
            owner.address = value if value else None
            owner.save(update_fields=['address'])
            return JsonResponse({'success': True, 'message': 'Address updated successfully!'})
    
    except Exception as e:
        import logging
        logger = logging.getLogger('clinic')
        logger.error(f"Error updating profile field {field}: {e}")
        return JsonResponse({'success': False, 'error': 'An error occurred. Please try again.'}, status=500)


@login_required
def change_password_request_otp(request):
    """Request OTP for password change from profile page.
    
    Security: Password can only be changed once per month.
    """
    import logging
    logger = logging.getLogger('clinic')
    logger.info(f"change_password_request_otp called - method: {request.method}, user: {request.user}")
    
    # Check rate limit for password changes
    owner = getattr(request.user, 'owner_profile', None)
    if owner:
        can_change, next_date = owner.can_change_password()
        if not can_change:
            messages.error(
                request, 
                f"You can only change your password once per month. "
                f"Next allowed change: {next_date.strftime('%B %d, %Y')}"
            )
            return redirect('profile')
    
    if request.method == 'POST':
        user = request.user
        logger.info(f"Processing OTP request for user: {user.email}")
        
        # Generate 6-digit OTP
        code = f"{random.randint(0, 999999):06d}"
        from .models import PasswordResetOTP
        # expire after 10 minutes
        expires = timezone.now() + timedelta(minutes=10)

        # Remove ALL previous unused OTPs for this user (including expired ones)
        deleted_count = PasswordResetOTP.objects.filter(user=user, is_used=False).delete()[0]
        logger.info(f"Deleted {deleted_count} old OTPs for user {user.id}")

        otp_obj = PasswordResetOTP.objects.create(user=user, code=code, expires_at=expires)
        logger.info(f"Created new OTP for user {user.id}: {code} (expires: {expires})")

        # Send email
        subject = f"Your {getattr(settings, 'BRAND_NAME', 'ePetCare')} password change verification code"
        ctx = {
            "code": code,
            "name": getattr(user, 'first_name', '') or user.username,
            "year": timezone.now().year,
            "BRAND_NAME": getattr(settings, 'BRAND_NAME', 'ePetCare'),
            "EMAIL_BRAND_LOGO_URL": getattr(settings, 'EMAIL_BRAND_LOGO_URL', ''),
        }
        message = render_to_string('clinic/auth/otp_email.txt', ctx)
        html_message = render_to_string('clinic/auth/otp_email.html', ctx)
        
        logger.info(f"Attempting to send email to {user.email}")
        try:
            from .utils.emailing import send_mail_http
            success = send_mail_http(subject, message, [user.email], settings.DEFAULT_FROM_EMAIL, html_message=html_message)
            if success:
                logger.info(f'Password change OTP email sent successfully to {user.email}')
            else:
                logger.error(f'Password change OTP email failed via HTTP provider')
                messages.error(request, 'Failed to send verification code. Please try again.')
                return redirect('profile')
        except Exception as e:
            logger.error(f'Password change OTP email failed: {e}')
            import traceback
            logger.error(f'Traceback: {traceback.format_exc()}')
            messages.error(request, 'Failed to send verification code. Please try again.')
            return redirect('profile')

        # Store user ID in session
        request.session['pw_change_user_id'] = user.id
        # Don't add messages.info here - template already shows "Enter the verification code sent to {{ email }}"
        return redirect('profile_verify_password_otp')

    return redirect('profile')


@login_required
def change_password_verify_otp(request):
    """Verify OTP for password change"""

    if request.method == 'POST':
        code = request.POST.get('otp', '').strip()
        from .models import PasswordResetOTP
        import logging
        logger = logging.getLogger('clinic')

        user_id = request.session.get('pw_change_user_id')

        # Debug output
        print(f"[DEBUG OTP] User session ID: {user_id}, Current user: {request.user.id}")
        print(f"[DEBUG OTP] Code received: '{code}' (length: {len(code)})")

        logger.info(f"OTP verification attempt - User ID from session: {user_id}, Current user: {request.user.id}, Code: '{code}', Code length: {len(code)}")

        if not user_id or user_id != request.user.id:
            messages.error(request, 'Session expired. Please try again.')
            return redirect('profile')

        otp_qs = PasswordResetOTP.objects.filter(user_id=user_id, code=code, is_used=False).order_by('-created_at')
        otp = otp_qs.first()

        print(f"[DEBUG OTP] OTP lookup result: {otp}")
        logger.info(f"OTP lookup result: {otp}")

        if not otp:
            # Clear all old messages first
            storage = messages.get_messages(request)
            storage.used = True
            # Add only the error message we want
            messages.error(request, 'Invalid verification code. Please try again.')
            logger.warning(f"No OTP found for user {user_id} with code '{code}'")
            # Check if any OTPs exist for this user
            all_otps = PasswordResetOTP.objects.filter(user_id=user_id, is_used=False).values('code', 'expires_at', 'created_at')
            print(f"[DEBUG OTP] Available unused OTPs: {list(all_otps)}")
            logger.info(f"Available unused OTPs for user: {list(all_otps)}")
            # Check if code exists but is marked as used
            used_otps = PasswordResetOTP.objects.filter(user_id=user_id, code=code, is_used=True).values('code', 'is_used', 'created_at')
            print(f"[DEBUG OTP] Used OTPs with this code: {list(used_otps)}")
            logger.info(f"Used OTPs with this code: {list(used_otps)}")
            return render(request, 'clinic/profile_verify_otp.html', {'email': request.user.email})
        elif otp.is_expired():
            messages.error(request, 'This code has expired. Please request a new one.')
            logger.warning(f"OTP expired - Created: {otp.created_at}, Expires: {otp.expires_at}")
            return redirect('profile')
        else:
            # Mark used and allow password change
            otp.is_used = True
            otp.attempts = otp.attempts + 1
            otp.save(update_fields=['is_used', 'attempts'])
            request.session['pw_change_verified'] = True
            logger.info(f"OTP verified successfully for user {user_id}")
            # Clear old messages and add success
            storage = messages.get_messages(request)
            storage.used = True
            messages.success(request, 'Email verified! Now set your new password.')
            return redirect('profile_set_new_password')

    # Clear any existing messages from previous pages on GET request
    storage = messages.get_messages(request)
    storage.used = True

    return render(request, 'clinic/profile_verify_otp.html', {'email': request.user.email})
@login_required
def change_password_set_new(request):
    """Set new password after OTP verification.
    
    Security: Updates last_password_change timestamp for rate limiting.
    """

    if not request.session.get('pw_change_verified'):
        messages.error(request, 'Please verify your email first.')
        return redirect('profile')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            
            # Update rate limit timestamp for password change
            owner = getattr(user, 'owner_profile', None)
            if owner:
                owner.last_password_change = timezone.now()
                owner.save(update_fields=['last_password_change'])
            
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            # Clear session flags
            request.session.pop('pw_change_user_id', None)
            request.session.pop('pw_change_verified', None)
            # Clear old messages and add success
            storage = messages.get_messages(request)
            storage.used = True
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    # Clear any existing messages to prevent notification bleed on GET
    storage = messages.get_messages(request)
    storage.used = True

    return render(request, 'clinic/profile_set_password.html', {'form': form})
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
    active_rx_count = pet.prescriptions.filter(is_active=True).count()

    return render(request, 'clinic/pet_detail.html', {
        "pet": pet,
        "appointments": appointments,
        "prescriptions": prescriptions,
        "medical_records": medical_records,
        "active_rx_count": active_rx_count,
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
    from django.utils import timezone
    
    # Auto-update missed appointments (past scheduled → missed)
    Appointment.update_missed_appointments()
    
    owner = getattr(request.user, 'owner_profile', None)
    appointments = Appointment.objects.select_related('pet').filter(pet__owner=owner).order_by('-date_time') if owner else Appointment.objects.none()
    # Get next upcoming appointment (earliest future appointment)
    next_appointment = Appointment.objects.select_related('pet').filter(
        pet__owner=owner,
        date_time__gte=timezone.now()
    ).order_by('date_time').first() if owner else None
    return render(request, 'clinic/appointment_list.html', {
        "appointments": appointments,
        "next_appointment": next_appointment
    })


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