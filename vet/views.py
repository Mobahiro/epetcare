from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import Veterinarian, VetNotification
from .forms import VetRegisterForm
from clinic.models import Owner, Pet, Appointment


def home(request):
    """Veterinarian portal home page"""
    return render(request, 'vet/home.html')


def register(request):
    """Register a new veterinarian"""
    if request.method == 'POST':
        form = VetRegisterForm(request.POST)
        if form.is_valid():
            try:
                user, vet, access_code = form.create_user_and_vet()
                
                # Send access code via email
                from django.core.mail import send_mail
                from django.conf import settings
                
                email_subject = "Your ePetCare Veterinarian Access Code"
                email_body = f"""
Dear {vet.full_name},

Welcome to ePetCare Veterinarian Portal!

Your registration is successful and pending admin approval. Once approved, you'll need the following credentials to login:

Username: {user.username}
Access Code: {access_code}

⚠️ IMPORTANT: Keep this access code secure! You will need it every time you login along with your password.

Your account will be activated once an administrator approves your registration.

Best regards,
ePetCare Team
                """
                
                try:
                    send_mail(
                        email_subject,
                        email_body,
                        settings.DEFAULT_FROM_EMAIL,
                        [vet.personal_email],
                        fail_silently=False,
                    )
                    email_sent = True
                except Exception as email_error:
                    print(f"Email send error: {email_error}")
                    email_sent = False
                
                if email_sent:
                    messages.success(
                        request, 
                        f"Registration successful! Your access code has been sent to {vet.personal_email}. "
                        "Keep this code secure - you'll need it to login. "
                        "Your account is pending admin approval."
                    )
                else:
                    messages.success(
                        request, 
                        f"Registration successful! Your access code is: {access_code} "
                        "(Save this code - you'll need it to login). "
                        "Your account is pending admin approval."
                    )
                
                return redirect('unified_login')
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
    else:
        form = VetRegisterForm()
    return render(request, 'vet/register.html', {"form": form})


def logout_view(request):
    """Log out a veterinarian"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('vet:home')


@login_required
def dashboard(request):
    """Veterinarian dashboard with patient stats and recent appointments"""
    vet = getattr(request.user, 'vet_profile', None)
    
    # Check if vet exists and is approved
    if vet and not vet.is_approved:
        logout(request)
        messages.warning(
            request, 
            "Your veterinarian account is pending approval. "
            "Please contact the administrator."
        )
        return redirect('unified_login')
    
    # Auto-update missed appointments (past scheduled → missed)
    Appointment.update_missed_appointments()
    
    # Get counts for dashboard stats
    total_owners = Owner.objects.count()
    total_pets = Pet.objects.count()
    upcoming_appointments = Appointment.objects.filter(
        status='scheduled'
    ).order_by('date_time')[:10]
    
    # Get recent notifications
    notifications = VetNotification.objects.filter(
        veterinarian=vet, 
        is_read=False
    )[:5] if vet else []
    
    context = {
        "vet": vet,
        "total_owners": total_owners,
        "total_pets": total_pets,
        "upcoming_appointments": upcoming_appointments,
        "notifications": notifications,
    }
    
    return render(request, 'vet/dashboard.html', context)


@login_required
def patients(request):
    """List all patients (pets) with their owners"""
    pets = Pet.objects.select_related('owner').order_by('owner__full_name', 'name')
    return render(request, 'vet/patients.html', {"pets": pets})


@login_required
def appointments(request):
    """List all appointments"""
    # Auto-update missed appointments (past scheduled → missed)
    Appointment.update_missed_appointments()
    
    appointments = Appointment.objects.select_related('pet', 'pet__owner').order_by('-date_time')
    return render(request, 'vet/appointments.html', {"appointments": appointments})


@login_required
def notifications(request):
    """List all notifications for the current veterinarian"""
    vet = getattr(request.user, 'vet_profile', None)
    notifications = VetNotification.objects.filter(veterinarian=vet) if vet else []
    
    # Mark all as read
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('vet:notifications')
        
    return render(request, 'vet/notifications.html', {"notifications": notifications})


@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    vet = getattr(request.user, 'vet_profile', None)
    if vet:
        try:
            notification = VetNotification.objects.get(id=notification_id, veterinarian=vet)
            notification.is_read = True
            notification.save()
            messages.success(request, "Notification marked as read.")
        except VetNotification.DoesNotExist:
            messages.error(request, "Notification not found.")
    
    return redirect('vet:notifications')


@login_required
def vet_profile(request):
    """Vet profile page with inline editing.
    
    Security policy:
    - Username: Can change once per month
    - Password: Can change once per month (requires OTP)
    - Full Name & License: Admin-only (contact epetcarewebsystem@gmail.com)
    - Phone/Bio/Specialization: Freely editable
    """
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        messages.error(request, "Veterinarian profile not found for your account.")
        return redirect('vet:dashboard')

    # Get rate limit status for display
    can_change_username, next_username_date = vet.can_change_username()
    can_change_email, next_email_date = vet.can_change_email()
    can_change_password, next_password_date = vet.can_change_password()

    return render(request, 'vet/profile.html', {
        'vet': vet,
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
    """AJAX endpoint for updating individual profile fields.
    
    Handles: username (rate-limited), phone, specialization, bio
    """
    from django.http import JsonResponse
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        return JsonResponse({'success': False, 'error': 'Veterinarian profile not found'}, status=404)
    
    field = request.POST.get('field')
    value = request.POST.get('value', '').strip()
    
    allowed_fields = ['username', 'phone', 'specialization', 'bio']
    if field not in allowed_fields:
        return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)
    
    try:
        if field == 'username':
            # Check rate limit
            can_change, next_date = vet.can_change_username()
            if not can_change:
                return JsonResponse({
                    'success': False, 
                    'error': f'Username can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.'
                }, status=403)
            
            # Validate username
            if not value:
                return JsonResponse({'success': False, 'error': 'Username cannot be empty'}, status=400)
            
            if len(value) < 3:
                return JsonResponse({'success': False, 'error': 'Username must be at least 3 characters'}, status=400)
            
            # Check uniqueness
            if User.objects.filter(username=value).exclude(pk=request.user.pk).exists():
                return JsonResponse({'success': False, 'error': 'This username is already taken'}, status=400)
            
            # Update username and timestamp
            request.user.username = value
            request.user.save(update_fields=['username'])
            vet.last_username_change = timezone.now()
            vet.save(update_fields=['last_username_change'])
            
            return JsonResponse({'success': True, 'message': 'Username updated successfully!'})
        
        elif field == 'phone':
            vet.phone = value or None
            vet.save(update_fields=['phone'])
            return JsonResponse({'success': True, 'message': 'Phone number updated successfully!'})
        
        elif field == 'specialization':
            vet.specialization = value or None
            vet.save(update_fields=['specialization'])
            return JsonResponse({'success': True, 'message': 'Specialization updated successfully!'})
        
        elif field == 'bio':
            vet.bio = value or None
            vet.save(update_fields=['bio'])
            return JsonResponse({'success': True, 'message': 'Bio updated successfully!'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Unknown error'}, status=500)


@login_required
def profile_request_field_otp(request):
    """Request OTP to verify profile field change (username).
    
    Sends OTP to vet's personal_email for verification.
    """
    from django.http import JsonResponse
    from clinic.models import PasswordResetOTP
    from clinic.utils.emailing import send_mail_http
    from django.template.loader import render_to_string
    import random
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        return JsonResponse({'success': False, 'error': 'Veterinarian profile not found'}, status=404)
    
    field = request.POST.get('field')
    value = request.POST.get('value', '').strip()
    
    # Only username requires OTP for vets
    if field != 'username':
        return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)
    
    # Validate new username
    if not value or len(value) < 3:
        return JsonResponse({'success': False, 'error': 'Username must be at least 3 characters'}, status=400)
    
    # Check rate limit
    can_change, next_date = vet.can_change_username()
    if not can_change:
        return JsonResponse({
            'success': False, 
            'error': f'Username can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.'
        }, status=403)
    
    # Check uniqueness
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if User.objects.filter(username=value).exclude(pk=request.user.pk).exists():
        return JsonResponse({'success': False, 'error': 'This username is already taken'}, status=400)
    
    # Get target email (personal_email)
    target_email = vet.personal_email
    if not target_email:
        return JsonResponse({'success': False, 'error': 'No personal email set. Contact admin.'}, status=400)
    
    # Generate OTP
    code = f"{random.randint(0, 999999):06d}"
    expires = timezone.now() + timedelta(minutes=10)
    
    # Clear old OTPs
    PasswordResetOTP.objects.filter(user=request.user, is_used=False).delete()
    PasswordResetOTP.objects.create(user=request.user, code=code, expires_at=expires)
    
    # Store pending change in session
    request.session['vet_profile_change_field'] = field
    request.session['vet_profile_change_value'] = value
    
    # Send email
    subject = f"ePetCare - Verify your profile change"
    ctx = {
        'code': code,
        'name': vet.full_name or request.user.username,
        'field': field,
        'new_value': value,
        'year': timezone.now().year,
        'BRAND_NAME': 'ePetCare',
    }
    message = render_to_string('vet/auth/profile_change_otp_email.txt', ctx)
    html_message = render_to_string('vet/auth/profile_change_otp_email.html', ctx)
    
    try:
        success = send_mail_http(subject, message, [target_email], settings.DEFAULT_FROM_EMAIL, html_message=html_message)
        if success:
            # Mask email for display
            parts = target_email.split('@')
            masked = parts[0][:2] + '***@' + parts[1] if len(parts) == 2 else target_email
            return JsonResponse({'success': True, 'masked_email': masked})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to send verification code'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Failed to send verification code'}, status=500)


@login_required
def profile_verify_field_otp(request):
    """Verify OTP and apply profile field change."""
    from django.http import JsonResponse
    from clinic.models import PasswordResetOTP
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        return JsonResponse({'success': False, 'error': 'Veterinarian profile not found'}, status=404)
    
    code = request.POST.get('code', '').strip()
    field = request.session.get('vet_profile_change_field')
    value = request.session.get('vet_profile_change_value')
    
    if not field or not value:
        return JsonResponse({'success': False, 'error': 'No pending change found'}, status=400)
    
    if not code or len(code) != 6:
        return JsonResponse({'success': False, 'error': 'Invalid code format'}, status=400)
    
    # Verify OTP
    try:
        otp = PasswordResetOTP.objects.get(
            user=request.user, 
            code=code, 
            is_used=False, 
            expires_at__gt=timezone.now()
        )
        otp.is_used = True
        otp.save()
    except PasswordResetOTP.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid or expired code'}, status=400)
    
    # Apply the change
    if field == 'username':
        request.user.username = value
        request.user.save(update_fields=['username'])
        vet.last_username_change = timezone.now()
        vet.save(update_fields=['last_username_change'])
    
    # Clear session
    request.session.pop('vet_profile_change_field', None)
    request.session.pop('vet_profile_change_value', None)
    
    return JsonResponse({'success': True, 'message': f'{field.title()} updated successfully!', 'new_value': value})


@login_required
def change_password_request_otp(request):
    """Request OTP for password change."""
    from django.http import JsonResponse
    from clinic.models import PasswordResetOTP
    from clinic.utils.emailing import send_mail_http
    from django.template.loader import render_to_string
    import random
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        messages.error(request, "Veterinarian profile not found.")
        return redirect('vet:profile')
    
    # Check rate limit
    can_change, next_date = vet.can_change_password()
    if not can_change:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': f'Password can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.'})
        messages.error(request, f'Password can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.')
        return redirect('vet:profile')
    
    if request.method == 'POST':
        target_email = vet.personal_email
        if not target_email:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'No personal email set. Contact admin.'})
            messages.error(request, 'No personal email set. Contact admin.')
            return redirect('vet:profile')
        
        # Generate OTP
        code = f"{random.randint(0, 999999):06d}"
        expires = timezone.now() + timedelta(minutes=10)
        
        # Clear old OTPs
        PasswordResetOTP.objects.filter(user=request.user, is_used=False).delete()
        PasswordResetOTP.objects.create(user=request.user, code=code, expires_at=expires)
        
        # Send email
        subject = f"ePetCare - Password change verification code"
        ctx = {
            'code': code,
            'name': vet.full_name or request.user.username,
            'year': timezone.now().year,
            'BRAND_NAME': 'ePetCare',
        }
        message = render_to_string('clinic/auth/otp_email.txt', ctx)
        html_message = render_to_string('clinic/auth/otp_email.html', ctx)
        
        try:
            success = send_mail_http(subject, message, [target_email], settings.DEFAULT_FROM_EMAIL, html_message=html_message)
            if success:
                request.session['vet_pw_change_user_id'] = request.user.id
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Verification code sent'})
                return redirect('vet:profile_verify_password_otp')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Failed to send verification code'})
                messages.error(request, 'Failed to send verification code. Please try again.')
                return redirect('vet:profile')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Failed to send verification code'})
            messages.error(request, 'Failed to send verification code. Please try again.')
            return redirect('vet:profile')
    
    return redirect('vet:profile')


@login_required
def change_password_verify_otp(request):
    """Verify OTP for password change."""
    from django.http import JsonResponse
    from clinic.models import PasswordResetOTP
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        messages.error(request, "Veterinarian profile not found.")
        return redirect('vet:profile')
    
    user_id = request.session.get('vet_pw_change_user_id')
    if user_id != request.user.id:
        messages.error(request, 'Invalid session. Please try again.')
        return redirect('vet:profile')
    
    if request.method == 'POST':
        code = request.POST.get('otp', '').strip()
        
        if not code or len(code) != 6:
            messages.error(request, 'Please enter a valid 6-digit code.')
            return render(request, 'vet/profile_verify_otp.html', {'email': vet.personal_email})
        
        try:
            otp = PasswordResetOTP.objects.get(
                user=request.user,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            otp.is_used = True
            otp.save()
            
            # Store verification in session
            request.session['vet_pw_otp_verified'] = True
            return redirect('vet:profile_set_new_password')
            
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid or expired code. Please try again.')
            return render(request, 'vet/profile_verify_otp.html', {'email': vet.personal_email})
    
    # Mask email for display
    email = vet.personal_email or ''
    if '@' in email:
        parts = email.split('@')
        masked_email = parts[0][:2] + '***@' + parts[1]
    else:
        masked_email = email
    
    return render(request, 'vet/profile_verify_otp.html', {'email': masked_email})


@login_required
def change_password_set_new(request):
    """Set new password after OTP verification."""
    from django.contrib.auth import update_session_auth_hash
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        messages.error(request, "Veterinarian profile not found.")
        return redirect('vet:profile')
    
    if not request.session.get('vet_pw_otp_verified'):
        messages.error(request, 'Please verify your email first.')
        return redirect('vet:profile')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validate password
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'vet/set_new_password.html')
        
        if not any(c.isdigit() for c in new_password):
            messages.error(request, 'Password must contain at least one number.')
            return render(request, 'vet/set_new_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'vet/set_new_password.html')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update rate limit
        vet.last_password_change = timezone.now()
        vet.save(update_fields=['last_password_change'])
        
        # Keep user logged in
        update_session_auth_hash(request, request.user)
        
        # Clear session
        request.session.pop('vet_pw_change_user_id', None)
        request.session.pop('vet_pw_otp_verified', None)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('vet:profile')
    
    return render(request, 'vet/set_new_password.html')