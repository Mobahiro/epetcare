"""
Custom login form for veterinarians requiring access code
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm


class VetLoginForm(forms.Form):
    """Login form that requires username, password, and access code"""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
    )
    access_code = forms.CharField(
        max_length=20,
        label="Access Code",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your access code'}),
        help_text="The unique code sent to your email during registration"
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        access_code = self.cleaned_data.get('access_code')

        if username and password:
            # First authenticate with username and password
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid username or password.",
                    code='invalid_login',
                )
            
            # Check if user is a vet
            if not hasattr(self.user_cache, 'vet_profile'):
                raise forms.ValidationError(
                    "This account is not registered as a veterinarian.",
                    code='not_vet',
                )
            
            # Verify access code
            vet = self.user_cache.vet_profile
            if vet.access_code != access_code:
                raise forms.ValidationError(
                    "Invalid access code. Please check your email for the correct code.",
                    code='invalid_code',
                )
            
            # Check if vet is approved
            if not vet.is_approved:
                raise forms.ValidationError(
                    "Your account is pending approval. Please contact the administrator.",
                    code='not_approved',
                )

        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache
