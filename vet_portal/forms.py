from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from vet.models import Veterinarian
from clinic.models import Appointment, MedicalRecord, Prescription
from .models import VetSchedule, Treatment, TreatmentRecord


class VetLoginForm(AuthenticationForm):
    """Custom login form for veterinarians"""

    def confirm_login_allowed(self, user):
        # Allow veterinarians, staff, or superusers to access the vet portal
        is_vet = hasattr(user, 'vet_profile')
        if not (is_vet or user.is_staff or user.is_superuser):
            raise forms.ValidationError(
                "This account does not have veterinarian privileges. "
                "Please contact the administrator."
            )


        super().confirm_login_allowed(user)


class VetRegistrationForm(UserCreationForm):
    """Form to register a new veterinarian User + profile.

    Uses Django's built-in password validation. Also captures vet full name
    and (optional) license number.
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False, max_length=150)
    last_name = forms.CharField(required=False, max_length=150)
    full_name = forms.CharField(required=True, max_length=120)
    license_number = forms.CharField(required=False, max_length=50)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def clean_username(self):
        """Validate username is unique"""
        username = self.cleaned_data.get("username", "").lower()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken")
        return username

    def clean_email(self):
        """Validate email is unique across all users"""
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered")
        # Also check if used as personal_email by a vet
        if Veterinarian.objects.filter(personal_email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered by another veterinarian")
        return email

    def clean_license_number(self):
        """Validate license number is unique if provided"""
        license_number = self.cleaned_data.get("license_number", "").strip()
        if license_number:
            if Veterinarian.objects.filter(license_number=license_number).exists():
                raise forms.ValidationError("This license number is already registered")
        return license_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        # Ensure normal active user
        user.is_active = True
        if commit:
            user.save()
            # Create Veterinarian profile
            from vet.models import Veterinarian
            Veterinarian.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                license_number=self.cleaned_data.get("license_number", "")
            )
        return user


class VetScheduleForm(forms.ModelForm):
    """Form for managing veterinarian schedules"""

    class Meta:
        model = VetSchedule
        fields = ['date', 'start_time', 'end_time', 'is_available', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


class AppointmentForm(forms.ModelForm):
    """Form for managing appointments"""

    class Meta:
        model = Appointment
        fields = ['pet', 'date_time', 'reason', 'notes', 'status']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class MedicalRecordForm(forms.ModelForm):
    """Form for managing medical records"""

    class Meta:
        model = MedicalRecord
        fields = ['pet', 'visit_date', 'condition', 'treatment', 'vet_notes']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PrescriptionForm(forms.ModelForm):
    """Form for managing prescriptions"""

    class Meta:
        model = Prescription
        fields = [
            'pet', 'medication_name', 'dosage', 'instructions',
            'date_prescribed', 'duration_days', 'is_active'
        ]
        widgets = {
            'date_prescribed': forms.DateInput(attrs={'type': 'date'}),
        }


class TreatmentForm(forms.ModelForm):
    """Form for managing treatments"""

    class Meta:
        model = Treatment
        fields = ['name', 'description', 'duration_minutes', 'price', 'is_active']


class TreatmentRecordForm(forms.ModelForm):
    """Form for recording treatments"""

    class Meta:
        model = TreatmentRecord
        fields = ['medical_record', 'treatment', 'notes', 'performed_by']
