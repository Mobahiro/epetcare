from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Owner, Pet, Appointment, Vaccination, MedicalRecord, Prescription


class OwnerForm(forms.ModelForm):
    """Form for editing owner contact information.
    
    Security policy:
    - full_name: Admin-only (cannot be changed by user, must contact epetcarewebsystem@gmail.com)
    - phone, address: Freely editable
    - email: Synced from User model, not directly editable here
    """
    class Meta:
        model = Owner
        fields = ["phone", "address"]  # Removed full_name - admin only


class OwnerFullNameForm(forms.ModelForm):
    """Admin-only form for editing owner's full name"""
    class Meta:
        model = Owner
        fields = ["full_name"]


class UserProfileForm(forms.ModelForm):
    """Form for editing user details like username and email.
    
    Security policy:
    - username: Can change once per month (rate limited)
    - email: Can change once per month (rate limited), requires OTP verification
    - first_name, last_name: Disabled (part of full_name, admin-only)
    """
    class Meta:
        model = User
        fields = ['username', 'email']
    
    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        
        # Check rate limits and disable fields if needed
        if owner:
            can_change_username, next_username_date = owner.can_change_username()
            can_change_email, next_email_date = owner.can_change_email()
            
            if not can_change_username:
                self.fields['username'].disabled = True
                self.fields['username'].help_text = f"You can change your username again after {next_username_date.strftime('%B %d, %Y')}"
            
            if not can_change_email:
                self.fields['email'].disabled = True
                self.fields['email'].help_text = f"You can change your email again after {next_email_date.strftime('%B %d, %Y')}"
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.owner and self.instance:
            # Check if username is actually being changed
            if username != self.instance.username:
                can_change, next_date = self.owner.can_change_username()
                if not can_change:
                    raise forms.ValidationError(
                        f"You can only change your username once per month. "
                        f"Next allowed change: {next_date.strftime('%B %d, %Y')}"
                    )
                # Check if username is already taken
                if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("This username is already taken.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
        if self.owner and self.instance:
            # Check if email is actually being changed
            if email != self.instance.email:
                can_change, next_date = self.owner.can_change_email()
                if not can_change:
                    raise forms.ValidationError(
                        f"You can only change your email once per month. "
                        f"Next allowed change: {next_date.strftime('%B %d, %Y')}"
                    )
                # Pet owners must use Gmail only
                if not email.endswith('@gmail.com'):
                    raise forms.ValidationError("Only Gmail addresses (@gmail.com) are allowed.")
                # Check if email is already taken
                if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("This email is already registered to another account.")
        return email


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
            "species",
            "custom_species",
            "breed",
            "sex",
            "birth_date",
            "weight_kg",
            "notes",
            "image",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "custom_species": forms.TextInput(attrs={"placeholder": "Specify your pet's species"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max date to today to prevent future dates
        from datetime import date
        self.fields['birth_date'].widget.attrs['max'] = date.today().isoformat()
        # Set maxlength for name and breed
        self.fields['name'].widget.attrs['maxlength'] = '25'
        self.fields['breed'].widget.attrs['maxlength'] = '35'
        self.fields['custom_species'].widget.attrs['maxlength'] = '50'
        self.fields['custom_species'].required = False
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) > 25:
            raise forms.ValidationError("Pet name cannot exceed 25 characters.")
        if len(name) < 1:
            raise forms.ValidationError("Pet name is required.")
        return name
    
    def clean_breed(self):
        breed = self.cleaned_data.get('breed', '').strip()
        if len(breed) > 35:
            raise forms.ValidationError("Breed cannot exceed 35 characters.")
        return breed
    
    def clean_birth_date(self):
        from datetime import date
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > date.today():
            raise forms.ValidationError("Birth date cannot be in the future.")
        return birth_date
    
    def clean(self):
        cleaned_data = super().clean()
        species = cleaned_data.get('species')
        custom_species = cleaned_data.get('custom_species', '').strip()
        
        # If species is "other", require custom_species
        if species == 'other' and not custom_species:
            self.add_error('custom_species', 'Please specify the species of your pet.')
        
        return cleaned_data


class PetCreateForm(forms.ModelForm):
    """Form used when adding a pet from the website.

    The owner is automatically set to the currently logged-in user's Owner
    profile in the view, so we intentionally exclude the 'owner' field here.
    """

    class Meta:
        model = Pet
        exclude = ["owner"]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "custom_species": forms.TextInput(attrs={"placeholder": "Specify your pet's species"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max date to today to prevent future dates
        from datetime import date
        self.fields['birth_date'].widget.attrs['max'] = date.today().isoformat()
        # Set maxlength for name and breed
        self.fields['name'].widget.attrs['maxlength'] = '25'
        self.fields['breed'].widget.attrs['maxlength'] = '35'
        self.fields['custom_species'].widget.attrs['maxlength'] = '50'
        self.fields['custom_species'].required = False
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) > 25:
            raise forms.ValidationError("Pet name cannot exceed 25 characters.")
        if len(name) < 1:
            raise forms.ValidationError("Pet name is required.")
        return name
    
    def clean_breed(self):
        breed = self.cleaned_data.get('breed', '').strip()
        if len(breed) > 35:
            raise forms.ValidationError("Breed cannot exceed 35 characters.")
        return breed
    
    def clean(self):
        cleaned_data = super().clean()
        species = cleaned_data.get('species')
        custom_species = cleaned_data.get('custom_species', '').strip()
        
        # If species is "other", require custom_species
        if species == 'other' and not custom_species:
            self.add_error('custom_species', 'Please specify the species of your pet.')
        
        return cleaned_data
    
    def clean_birth_date(self):
        from datetime import date
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > date.today():
            raise forms.ValidationError("Birth date cannot be in the future.")
        return birth_date


from django.utils import timezone
from datetime import timedelta


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["pet", "date_time", "reason", "notes"]
        widgets = {
            "date_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
    
    def clean_date_time(self):
        """Validate that appointment date/time meets requirements."""
        date_time = self.cleaned_data.get('date_time')
        if date_time:
            now = timezone.now()
            
            # FIRST: Check business hours (8 AM - 6 PM) - clinic must be open
            hour = date_time.hour
            if hour < 8 or hour >= 18:
                raise forms.ValidationError(
                    "Our clinic is open from 8:00 AM to 6:00 PM only. "
                    "Please select a time within business hours."
                )
            
            # SECOND: Require at least 2 hours advance booking
            min_booking_time = now + timezone.timedelta(hours=2)
            if date_time < min_booking_time:
                raise forms.ValidationError(
                    "Appointments must be scheduled at least 2 hours in advance. "
                    "Please select a later time."
                )
            
            # THIRD: Don't allow appointments more than 6 months in advance
            max_future = now + timezone.timedelta(days=180)
            if date_time > max_future:
                raise forms.ValidationError(
                    "Appointments can only be scheduled up to 6 months in advance."
                )
        
        return date_time
    
    def clean(self):
        """Cross-field validation to check for duplicate appointment times."""
        cleaned_data = super().clean()
        date_time = cleaned_data.get('date_time')
        pet = cleaned_data.get('pet')
        
        if date_time and pet:
            # Get the owner's branch to check appointments in same branch
            branch = pet.owner.branch
            
            # Define time window (30 minutes before and after)
            time_window = timedelta(minutes=30)
            window_start = date_time - time_window
            window_end = date_time + time_window
            
            # Check for existing appointments in the same branch within the time window
            # Only check scheduled appointments (not cancelled or completed)
            conflicting_appointments = Appointment.objects.filter(
                pet__owner__branch=branch,
                date_time__gte=window_start,
                date_time__lte=window_end,
                status='scheduled'
            )
            
            # Exclude current instance if editing an existing appointment
            if self.instance and self.instance.pk:
                conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)
            
            if conflicting_appointments.exists():
                conflict = conflicting_appointments.first()
                raise forms.ValidationError(
                    f"This time slot is not available. There is already an appointment scheduled "
                    f"at {conflict.date_time.strftime('%I:%M %p')} for {conflict.pet.name}. "
                    f"Please choose a different time (at least 30 minutes apart)."
                )
        
        return cleaned_data


class VaccinationForm(forms.ModelForm):
    class Meta:
        model = Vaccination
        fields = ["pet", "vaccine_name", "date_given", "next_due", "notes"]
        widgets = {
            "date_given": forms.DateInput(attrs={"type": "date"}),
            "next_due": forms.DateInput(attrs={"type": "date"}),
        }


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ["pet", "visit_date", "condition", "treatment", "vet_notes"]
        widgets = {
            "visit_date": forms.DateInput(attrs={"type": "date"}),
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = [
            "pet",
            "medication_name",
            "dosage",
            "instructions",
            "date_prescribed",
            "duration_days",
            "is_active",
        ]
        widgets = {
            "date_prescribed": forms.DateInput(attrs={"type": "date"}),
        }
import re

class RegisterForm(forms.Form):
    username = forms.CharField(
        min_length=3,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Choose a username', 'maxlength': '30'}),
        help_text="3-30 characters. Letters, numbers, and underscores only."
    )
    email = forms.CharField(
        max_length=254,
        label="Email",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'type': 'email', 'placeholder': 'your@gmail.com', 'maxlength': '254'}),
        help_text="Pet owners: Gmail addresses only (@gmail.com)"
    )
    personal_email = forms.EmailField(
        label="Personal Email (for Vets only)",
        required=False,
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'your.real.email@gmail.com', 'maxlength': '254'})
    )
    password1 = forms.CharField(
        min_length=8,
        max_length=128,
        label="Password", 
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Enter password', 'maxlength': '128'}),
        help_text="8-128 characters. Must include uppercase, lowercase, number, and special character."
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Re-enter password', 'maxlength': '128'})
    )
    full_name = forms.CharField(
        min_length=2,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Your full name', 'maxlength': '50'}),
        help_text="2-50 characters. Letters, spaces, and hyphens only."
    )
    specialization = forms.CharField(
        max_length=50, 
        required=False, 
        label="Specialization (Vets only)",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'e.g., Small Animals, Surgery', 'maxlength': '50'})
    )
    license_number = forms.CharField(
        max_length=30, 
        required=False, 
        label="License Number (Vets only)",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Your license number', 'maxlength': '30'})
    )
    phone = forms.CharField(
        min_length=11,
        max_length=12, 
        required=False,  # Made optional - validated in clean() for pet owners only
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': '09xxxxxxxxx or 63xxxxxxxxxx', 'maxlength': '12', 'pattern': '[0-9]{11,12}', 'inputmode': 'numeric'}),
        help_text="Philippine mobile number: 09xxxxxxxxx (11 digits) or 63xxxxxxxxxx (12 digits)"
    )
    address = forms.CharField(
        min_length=5,
        max_length=255,
        widget=forms.Textarea(attrs={'class': 'auth-input', 'rows': 3, 'placeholder': 'Your complete address', 'maxlength': '255'}), 
        required=False,  # Made optional - validated in clean() for pet owners only
        label="Address"
    )
    branch = forms.ChoiceField(
        choices=[
            ('taguig', 'Taguig'),
            ('pasig', 'Pasig'),
            ('makati', 'Makati'),
        ],
        required=False,  # Not required - pet owners select after OTP, vets get branch from email
        label="Preferred Branch (Pet Owners)",
        widget=forms.Select(attrs={'class': 'auth-input'}),
        help_text="Select your preferred vet clinic branch location"
    )
    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms & Privacy Notice",
        error_messages={
            'required': 'You must accept the Terms & Privacy Notice to register.'
        }
    )
    
    # Branch keywords for vet registration (check for branch name followed by @vet)
    VET_BRANCH_KEYWORDS = ['taguig@vet', 'pasig@vet', 'makati@vet']

    def clean_username(self):
        username = self.cleaned_data.get("username", "").lower()
        # Only allow letters, numbers, and underscores - no spaces
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError("Username can only contain letters, numbers, and underscores. No spaces allowed.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username

    def clean_full_name(self):
        full_name = self.cleaned_data.get("full_name", "").strip()
        # Only allow letters, spaces, and hyphens
        if not re.match(r'^[a-zA-Z\s\-]+$', full_name):
            raise forms.ValidationError("Full name can only contain letters, spaces, and hyphens.")
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        
        # Skip validation if empty (will be validated in clean() for pet owners)
        if not phone:
            return phone
        
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Check valid formats: 09xxxxxxxxx (11 digits) or 63xxxxxxxxxx (12 digits)
        if phone.startswith('09'):
            if len(phone) != 11:
                raise forms.ValidationError("Phone number starting with 09 must be exactly 11 digits")
        elif phone.startswith('63'):
            if len(phone) != 12:
                raise forms.ValidationError("Phone number starting with 63 must be exactly 12 digits")
        else:
            raise forms.ValidationError("Phone number must start with 09 or 63")
        
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get("password1", "")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        
        # Check for at least one digit
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password must contain at least one number.")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
            raise forms.ValidationError("Password must contain at least one special character (!@#$%^&*etc).")
        
        # No whitespace
        if re.search(r'\s', password):
            raise forms.ValidationError("Password cannot contain spaces.")
        
        return password

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        
        # Check if it's a vet registration email (any branch keyword)
        is_vet_email = any(keyword in email for keyword in self.VET_BRANCH_KEYWORDS)
        
        # If not vet email, validate as normal email
        if not is_vet_email:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                validate_email(email)
            except DjangoValidationError:
                raise forms.ValidationError("Enter a valid email address.")
            
            # Pet owners must use Gmail only
            if not email.endswith('@gmail.com'):
                raise forms.ValidationError("Only Gmail addresses (@gmail.com) are allowed for pet owner registration.")
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        email = cleaned_data.get("email", "").lower()
        personal_email = cleaned_data.get("personal_email")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match")
        
        # Check if registering as vet (any branch keyword)
        is_vet_registration = any(keyword in email for keyword in self.VET_BRANCH_KEYWORDS)
        
        if is_vet_registration:
            # Personal email is required for vets
            if not personal_email:
                self.add_error("personal_email", "Personal email is required for vet registration to receive your access code")
            
            # Specialization is required for vets
            specialization = cleaned_data.get("specialization", "").strip()
            if not specialization:
                self.add_error("specialization", "Specialization is required for veterinarian registration")
            
            # License number is required for vets and must be unique
            license_number = cleaned_data.get("license_number", "").strip()
            if not license_number:
                self.add_error("license_number", "License number is required for veterinarian registration")
            else:
                # Check uniqueness of license number
                from vet.models import Veterinarian
                if Veterinarian.objects.filter(license_number=license_number).exists():
                    self.add_error("license_number", "This license number is already registered")
        else:
            # Pet owner registration - phone and address are required
            phone = cleaned_data.get("phone", "").strip()
            address = cleaned_data.get("address", "").strip()
            
            if not phone:
                self.add_error("phone", "Phone number is required for pet owner registration")
            if not address:
                self.add_error("address", "Address is required for pet owner registration")

        return cleaned_data
    
    def is_vet_registration(self):
        """Check if this is a vet registration based on email (any branch keyword)"""
        email = self.cleaned_data.get("email", "").lower()
        return any(keyword in email for keyword in self.VET_BRANCH_KEYWORDS)
    
    def get_vet_branch(self):
        """Extract branch from vet email keyword"""
        email = self.cleaned_data.get("email", "").lower()
        if "taguig@vet" in email:
            return "taguig"
        elif "pasig@vet" in email:
            return "pasig"
        elif "makati@vet" in email:
            return "makati"
        return "taguig"  # default
    
    def generate_access_code(self):
        """Generate a unique 8-character access code for vets"""
        import secrets
        import string
        from vet.models import Veterinarian
        
        while True:
            letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))
            digits = ''.join(secrets.choice(string.digits) for _ in range(5))
            code = f"{letters}{digits}"
            
            if not Veterinarian.objects.filter(access_code=code).exists():
                return code

    def create_user_and_owner(self):
        username = self.cleaned_data["username"].lower()
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        full_name = self.cleaned_data["full_name"]
        phone = self.cleaned_data.get("phone", "")
        address = self.cleaned_data.get("address", "")
        branch = self.cleaned_data.get("branch", "taguig")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        owner = Owner.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            branch=branch
        )

        return user, owner
    
    def create_user_and_vet(self):
        """Create vet account when branch keyword is detected in email"""
        from vet.models import Veterinarian
        
        username = self.cleaned_data["username"].lower()
        email = self.cleaned_data["email"].lower()
        personal_email = self.cleaned_data["personal_email"]
        password = self.cleaned_data["password1"]
        full_name = self.cleaned_data["full_name"]
        specialization = self.cleaned_data.get("specialization", "")
        license_number = self.cleaned_data.get("license_number", "")
        phone = self.cleaned_data.get("phone", "")
        branch = self.get_vet_branch()  # Extract branch from email keyword

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        access_code = self.generate_access_code()

        vet = Veterinarian.objects.create(
            user=user,
            full_name=full_name,
            specialization=specialization,
            license_number=license_number,
            phone=phone,
            access_code=access_code,
            personal_email=personal_email,
            branch=branch
        )

        return user, vet, access_code


class PasswordResetRequestForm(PasswordResetForm):
    """Password reset form that accepts either email or username.

    Django's default PasswordResetForm expects an email. Many users type their
    username instead, which results in no email being sent. This subclass
    resolves that by matching on email (case-insensitive) OR username.
    
    Security: Validates that the email/username exists in the system.
    """

    def get_users(self, email):  # 'email' is the input value from the single field
        value = (email or '').strip()
        UserModel = get_user_model()

        # Base queryset: active users only
        qs = UserModel._default_manager.filter(is_active=True)

        if '@' in value:
            candidates = qs.filter(email__iexact=value)
        else:
            candidates = qs.filter(username__iexact=value)

        # Only users with usable passwords
        return [u for u in candidates if u.has_usable_password()]
    
    def clean_email(self):
        """Validate that the email or username exists in the system."""
        value = self.cleaned_data.get('email', '').strip()
        
        if not value:
            raise forms.ValidationError("Please enter your email or username.")
        
        users = list(self.get_users(value))
        
        if not users:
            if '@' in value:
                raise forms.ValidationError(
                    "This email is not registered in our system. "
                    "Please check the email address or create a new account."
                )
            else:
                raise forms.ValidationError(
                    "This username is not registered in our system. "
                    "Please check the username or try your email address instead."
                )
        
        return value


class PasswordResetOTPForm(forms.Form):
    """Form for entering the OTP code sent to email."""
    otp = forms.CharField(label="OTP Code", max_length=6, min_length=6)


class PasswordResetSetNewForm(SetPasswordForm):
    """Leverage Django's SetPasswordForm for new password validation."""
    pass