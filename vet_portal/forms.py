from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from vet.models import Veterinarian
from clinic.models import Appointment, MedicalRecord, Prescription
from .models import VetSchedule, Treatment, TreatmentRecord


class VetLoginForm(AuthenticationForm):
    """Custom login form for veterinarians"""
    
    def confirm_login_allowed(self, user):
        # Check if user is a veterinarian
        if not hasattr(user, 'vet_profile'):
            raise forms.ValidationError(
                "This account does not have veterinarian privileges. "
                "Please contact the administrator."
            )
        
        
        super().confirm_login_allowed(user)


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
