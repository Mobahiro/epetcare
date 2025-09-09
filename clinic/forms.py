from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Owner, Pet, Appointment, Vaccination, MedicalRecord, Prescription


class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ["full_name", "email", "phone", "address"]


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "owner",
            "name",
            "species",
            "breed",
            "sex",
            "birth_date",
            "weight_kg",
            "notes",
        ]
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