from django.contrib import admin
from .models import Owner, Pet, Appointment, Vaccination, MedicalRecord, Prescription


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "created_at")
    search_fields = ("full_name", "email", "phone")


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "species", "breed", "sex")
    list_filter = ("species", "sex")
    search_fields = ("name", "breed", "owner__full_name")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("pet", "date_time", "reason", "status")
    list_filter = ("status",)
    search_fields = ("pet__name", "reason")


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ("pet", "vaccine_name", "date_given", "next_due")
    search_fields = ("pet__name", "vaccine_name")


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("pet", "visit_date", "condition")
    search_fields = ("pet__name", "condition")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("pet", "medication_name", "date_prescribed", "is_active")
    list_filter = ("is_active",)
    search_fields = ("pet__name", "medication_name")
