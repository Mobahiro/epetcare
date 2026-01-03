from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
import random

User = get_user_model()


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
        return redirect('vet_portal:dashboard')

    # Get rate limit status for display
    can_change_username, next_username_date = vet.can_change_username()
    can_change_email, next_email_date = vet.can_change_email()
    can_change_password, next_password_date = vet.can_change_password()

    return render(request, 'vet_portal/profile.html', {
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
    from clinic.models import PasswordResetOTP
    from clinic.utils.emailing import send_mail_http
    
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
    message = f"Your verification code to change your {field} is: {code}\n\nThis code will expire in 10 minutes."
    html_message = render_to_string('vet_portal/auth/profile_change_otp_email.html', ctx)
    
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
    from clinic.models import PasswordResetOTP
    from clinic.utils.emailing import send_mail_http
    
    if request.method != 'POST':
        return redirect('vet_portal:profile')
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Veterinarian profile not found'})
        messages.error(request, "Veterinarian profile not found.")
        return redirect('vet_portal:profile')
    
    # Check rate limit
    can_change, next_date = vet.can_change_password()
    if not can_change:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': f'Password can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.'})
        messages.error(request, f'Password can only be changed once per month. Try again after {next_date.strftime("%B %d, %Y")}.')
        return redirect('vet_portal:profile')
    
    target_email = vet.personal_email
    if not target_email:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'No personal email set. Contact admin.'})
        messages.error(request, 'No personal email set. Contact admin.')
        return redirect('vet_portal:profile')
    
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
    message = f"Your verification code is: {code}\n\nThis code will expire in 10 minutes."
    html_message = render_to_string('clinic/auth/otp_email.html', ctx)
    
    try:
        success = send_mail_http(subject, message, [target_email], settings.DEFAULT_FROM_EMAIL, html_message=html_message)
        if success:
            request.session['vet_pw_change_user_id'] = request.user.id
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Verification code sent'})
            messages.success(request, 'Verification code sent to your email!')
            return redirect('vet_portal:profile_verify_password_otp')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Failed to send verification code'})
            messages.error(request, 'Failed to send verification code. Please try again.')
            return redirect('vet_portal:profile')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Failed to send verification code'})
        messages.error(request, 'Failed to send verification code. Please try again.')
        return redirect('vet_portal:profile')


@login_required
def change_password_verify_otp(request):
    """Verify OTP for password change."""
    from clinic.models import PasswordResetOTP
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        messages.error(request, "Veterinarian profile not found.")
        return redirect('vet_portal:profile')
    
    user_id = request.session.get('vet_pw_change_user_id')
    if user_id != request.user.id:
        messages.error(request, 'Invalid session. Please try again.')
        return redirect('vet_portal:profile')
    
    if request.method == 'POST':
        code = request.POST.get('otp', '').strip()
        
        if not code or len(code) != 6:
            messages.error(request, 'Please enter a valid 6-digit code.')
            return render(request, 'vet_portal/profile_verify_otp.html', {'email': vet.personal_email})
        
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
            return redirect('vet_portal:profile_set_new_password')
            
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid or expired code. Please try again.')
            return render(request, 'vet_portal/profile_verify_otp.html', {'email': vet.personal_email})
    
    # Mask email for display
    email = vet.personal_email or ''
    if '@' in email:
        parts = email.split('@')
        masked_email = parts[0][:2] + '***@' + parts[1]
    else:
        masked_email = email
    
    return render(request, 'vet_portal/profile_verify_otp.html', {'email': masked_email})


@login_required
def change_password_set_new(request):
    """Set new password after OTP verification."""
    import re
    
    vet = getattr(request.user, 'vet_profile', None)
    if not vet:
        messages.error(request, "Veterinarian profile not found.")
        return redirect('vet_portal:profile')
    
    if not request.session.get('vet_pw_otp_verified'):
        messages.error(request, 'Please verify your email first.')
        return redirect('vet_portal:profile')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'vet_portal/set_new_password.html')
        
        # Check new password is different from current
        if current_password == new_password:
            messages.error(request, 'New password must be different from your current password.')
            return render(request, 'vet_portal/set_new_password.html')
        
        # Validate password requirements
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'vet_portal/set_new_password.html')
        
        if not re.search(r'[A-Z]', new_password):
            messages.error(request, 'Password must contain at least one uppercase letter.')
            return render(request, 'vet_portal/set_new_password.html')
        
        if not re.search(r'[0-9]', new_password):
            messages.error(request, 'Password must contain at least one number.')
            return render(request, 'vet_portal/set_new_password.html')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/`~]', new_password):
            messages.error(request, 'Password must contain at least one special character (!@#$%^&*).')
            return render(request, 'vet_portal/set_new_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'vet_portal/set_new_password.html')
        
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
        return redirect('vet_portal:profile')
    
    return render(request, 'vet_portal/set_new_password.html')
