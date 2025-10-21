from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from .models import Owner, Pet, Appointment, Vaccination, MedicalRecord, Prescription


class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ["full_name", "email", "phone", "address"]


class UserProfileForm(forms.ModelForm):
    """Form for editing user details like username and email"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
            "species",
            "breed",
            "sex",
            "birth_date",
            "weight_kg",
            "notes",
            "image",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }


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
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["pet", "date_time", "reason", "notes", "status"]
        widgets = {
            "date_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


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


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    full_name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=30, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms & Privacy Notice",
        error_messages={
            'required': 'You must accept the Terms & Privacy Notice to register.'
        }
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").lower()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match")

        # accept_terms is handled automatically by field, but we keep placeholder for any audits/logging

        return cleaned_data

    def create_user_and_owner(self):
        username = self.cleaned_data["username"].lower()
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        full_name = self.cleaned_data["full_name"]
        phone = self.cleaned_data.get("phone", "")
        address = self.cleaned_data.get("address", "")

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
            address=address
        )

        return user, owner


class PasswordResetRequestForm(PasswordResetForm):
    """Password reset form that accepts either email or username.

    Django's default PasswordResetForm expects an email. Many users type their
    username instead, which results in no email being sent. This subclass
    resolves that by matching on email (case-insensitive) OR username.
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


class PasswordResetOTPForm(forms.Form):
    """Form for entering the OTP code sent to email."""
    otp = forms.CharField(label="OTP Code", max_length=6, min_length=6)


class PasswordResetSetNewForm(SetPasswordForm):
    """Leverage Django's SetPasswordForm for new password validation."""
    pass