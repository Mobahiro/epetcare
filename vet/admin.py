from django.contrib import admin
from .models import Veterinarian, VetNotification


@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialization", "license_number", "created_at")
    search_fields = ("full_name", "specialization", "license_number")


@admin.register(VetNotification)
class VetNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "veterinarian", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("title", "message", "veterinarian__full_name")