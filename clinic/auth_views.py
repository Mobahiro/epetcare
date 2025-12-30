"""
Unified authentication views for ePetCare
Handles login for both pet owners and veterinarians from a single endpoint
"""
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from vet.login_forms import VetLoginForm


class UnifiedLoginView:
    """
    Unified login view that handles authentication for both
    pet owners and veterinarians, routing them to appropriate dashboards
    """
    
    @staticmethod
    def get(request):
        if request.user.is_authenticated:
            return UnifiedLoginView._redirect_authenticated_user(request.user)
        
        form = AuthenticationForm()
        
        return render(request, 'clinic/auth/unified_login.html', {
            'form': form,
            'is_vet_login': False
        })
    
    @staticmethod
    def post(request):
        # Check if this is a vet login attempt
        is_vet_login = request.POST.get('login_type') == 'vet'
        
        if is_vet_login:
            # Vet login with access code
            form = VetLoginForm(request, data=request.POST)
            
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                messages.success(request, f"Welcome back, Dr. {user.vet_profile.full_name}!")
                return UnifiedLoginView._redirect_authenticated_user(user)
            else:
                # Return with form errors
                return render(request, 'clinic/auth/unified_login.html', {
                    'form': form,
                    'is_vet_login': is_vet_login
                })
        else:
            # Regular pet owner login
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            
            if username and password:
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    # Check if user is actually a vet (they must provide access code)
                    if hasattr(user, 'vet_profile'):
                        messages.error(
                            request,
                            "This is a veterinarian account. Please enter your access code to login."
                        )
                        form = AuthenticationForm()
                        return render(request, 'clinic/auth/unified_login.html', {
                            'form': form,
                            'is_vet_login': False
                        })
                    
                    # Login the pet owner
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.username}!")
                    return UnifiedLoginView._redirect_authenticated_user(user)
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Please enter both username and password.")
            
            form = AuthenticationForm()
            return render(request, 'clinic/auth/unified_login.html', {
                'form': form,
                'is_vet_login': False
            })
    
    @staticmethod
    def _redirect_authenticated_user(user):
        """Route user to their appropriate dashboard based on role"""
        # Check if user is a veterinarian
        if hasattr(user, 'vet_profile'):
            return redirect('vet_portal:dashboard')
        # Check if user is a pet owner
        elif hasattr(user, 'owner_profile'):
            return redirect('dashboard')
        # Superuser/admin
        elif user.is_superuser or user.is_staff:
            return redirect('/admin/')
        else:
            # Default fallback
            return redirect('home')


def unified_login(request):
    """Unified login view function"""
    if request.method == 'POST':
        return UnifiedLoginView.post(request)
    return UnifiedLoginView.get(request)
