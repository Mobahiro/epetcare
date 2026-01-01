from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model

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
