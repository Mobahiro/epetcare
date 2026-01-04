from django import forms
from django.contrib.auth.models import User
from .models import Veterinarian
import secrets
import string

# Secret registration key (only vets should know this)
VET_REGISTRATION_KEY = "VETACCESS2025"


class VetRegisterForm(forms.Form):
    registration_key = forms.CharField(
        max_length=50,
        label="Veterinarian Registration Key",
        widget=forms.TextInput(attrs={'placeholder': 'Enter the secret registration key'}),
        help_text="Contact the administrator if you don't have the registration key"
    )
    username = forms.CharField(max_length=150, label="Username")
    email = forms.CharField(
        max_length=254,
        label="Email",
        widget=forms.TextInput(attrs={'placeholder': 'yourname_pasig@vet'}),
        help_text="Use format: yourname_BRANCH@vet (e.g., kiyo_pasig@vet, kiyo_taguig@vet, kiyo_makati@vet)"
    )
    personal_email = forms.EmailField(
        label="Personal Email (Gmail, Yahoo, etc.)",
        help_text="Your access code will be sent to this real email address",
        required=False
    )
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    full_name = forms.CharField(max_length=120)
    specialization = forms.CharField(max_length=120, required=False)
    license_number = forms.CharField(max_length=50, required=False)
    phone = forms.CharField(max_length=30, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms & Privacy Notice",
        error_messages={'required': 'You must accept the Terms & Privacy Notice to register.'}
    )
    
    def clean_registration_key(self):
        key = self.cleaned_data.get("registration_key", "")
        if key != VET_REGISTRATION_KEY:
            raise forms.ValidationError(
                "Invalid registration key. Only authorized veterinarians can register. "
                "Please contact the administrator."
            )
        return key

    def clean_username(self):
        username = self.cleaned_data.get("username", "").lower()
        
        # Check if username already exists (case-insensitive)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username already exists")
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        
        # Check if it has a valid vet branch keyword
        valid_keywords = ['taguig@vet', 'pasig@vet', 'makati@vet']
        if not any(keyword in email for keyword in valid_keywords):
            raise forms.ValidationError(
                "Email must contain a branch keyword (taguig@vet, pasig@vet, or makati@vet). "
                "Example: kiyo_pasig@vet"
            )
        
        # Check if this vet email is already used (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This vet email is already registered by another veterinarian")
        
        return email
    
    def clean_phone(self):
        """Validate phone number is unique across all owners and vets"""
        phone = self.cleaned_data.get("phone", "").strip()
        
        if not phone:
            return phone
        
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Check phone uniqueness across Owner accounts
        from clinic.models import Owner
        if Owner.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already registered by a pet owner")
        
        # Check phone uniqueness across Veterinarian accounts
        if Veterinarian.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already registered by another veterinarian")
        
        return phone
    
    def clean_personal_email(self):
        """Validate personal email is unique across all users and vets"""
        personal_email = self.cleaned_data.get("personal_email", "").strip().lower()
        
        if not personal_email:
            return personal_email
        
        # Check if personal email is used by any User account
        if User.objects.filter(email__iexact=personal_email).exists():
            raise forms.ValidationError("This email is already registered to another account")
        
        # Check if personal email is used by another veterinarian
        if Veterinarian.objects.filter(personal_email__iexact=personal_email).exists():
            raise forms.ValidationError("This personal email is already registered by another veterinarian")
        
        return personal_email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        personal_email = cleaned_data.get("personal_email", "")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match")
        
        # Personal email is always required for vet registration
        if not personal_email:
            self.add_error("personal_email", "Personal email is required for veterinarian registration to send your access code")

        return cleaned_data

    def generate_access_code(self):
        """Generate a unique 8-character access code"""
        while True:
            # Generate code: 3 letters + 5 digits (e.g., ABC12345)
            letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))
            digits = ''.join(secrets.choice(string.digits) for _ in range(5))
            code = f"{letters}{digits}"
            
            # Ensure it's unique
            if not Veterinarian.objects.filter(access_code=code).exists():
                return code
    
    def create_user_and_vet(self):
        username = self.cleaned_data["username"].lower()
        email = self.cleaned_data["email"].lower()  # kiyo_pasig@vet or kiyo_taguig@vet
        personal_email = self.cleaned_data["personal_email"]  # real Gmail
        password = self.cleaned_data["password1"]
        full_name = self.cleaned_data["full_name"]
        specialization = self.cleaned_data.get("specialization", "")
        license_number = self.cleaned_data.get("license_number", "")
        phone = self.cleaned_data.get("phone", "")
        bio = self.cleaned_data.get("bio", "")
        
        # Extract branch from email
        if 'pasig@vet' in email:
            branch = 'pasig'
        elif 'makati@vet' in email:
            branch = 'makati'
        else:
            branch = 'taguig'  # default

        # Create user with the vet email
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Generate unique access code
        access_code = self.generate_access_code()

        vet = Veterinarian.objects.create(
            user=user,
            full_name=full_name,
            specialization=specialization,
            license_number=license_number,
            phone=phone,
            bio=bio,
            access_code=access_code,
            personal_email=personal_email,
            branch=branch  # Set branch from email
        )

        return user, vet, access_code

class VetProfileForm(forms.ModelForm):
    """Form for editing veterinarian contact information.
    
    Security policy:
    - full_name: Admin-only (cannot be changed by vet, must contact epetcarewebsystem@gmail.com)
    - license_number: Admin-only
    - phone, bio, specialization: Freely editable
    """
    class Meta:
        model = Veterinarian
        fields = ["phone", "specialization", "bio"]


class VetUserProfileForm(forms.ModelForm):
    """Form for editing vet user account details.
    
    Security policy:
    - username: Can change once per month (rate limited)
    - email: Can change once per month (rate limited)
    """
    class Meta:
        model = User
        fields = ['username']
    
    def __init__(self, *args, vet=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vet = vet
        
        # Check rate limits and disable fields if needed
        if vet:
            can_change_username, next_username_date = vet.can_change_username()
            
            if not can_change_username:
                self.fields['username'].disabled = True
                self.fields['username'].help_text = f"You can change your username again after {next_username_date.strftime('%B %d, %Y')}"
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.vet and self.instance:
            # Check if username is actually being changed
            if username != self.instance.username:
                can_change, next_date = self.vet.can_change_username()
                if not can_change:
                    raise forms.ValidationError(
                        f"You can only change your username once per month. "
                        f"Next allowed change: {next_date.strftime('%B %d, %Y')}"
                    )
                # Check if username is already taken
                if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("This username is already taken.")
        return username