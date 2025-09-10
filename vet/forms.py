from django import forms
from django.contrib.auth.models import User
from .models import Veterinarian


class VetRegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    full_name = forms.CharField(max_length=120)
    specialization = forms.CharField(max_length=120, required=False)
    license_number = forms.CharField(max_length=50, required=False)
    phone = forms.CharField(max_length=30, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

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

    def create_user_and_vet(self):
        username = self.cleaned_data["username"].lower()
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        full_name = self.cleaned_data["full_name"]
        specialization = self.cleaned_data.get("specialization", "")
        license_number = self.cleaned_data.get("license_number", "")
        phone = self.cleaned_data.get("phone", "")
        bio = self.cleaned_data.get("bio", "")
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        vet = Veterinarian.objects.create(
            user=user,
            full_name=full_name,
            specialization=specialization,
            license_number=license_number,
            phone=phone,
            bio=bio
        )
        
        return user, vet
