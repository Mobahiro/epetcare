from django.contrib import admin
from .models import VetPortalSettings, VetSchedule, Treatment, TreatmentRecord, OfflineChange

@admin.register(VetPortalSettings)
class VetPortalSettingsAdmin(admin.ModelAdmin):
    list_display = ['last_sync_time', 'offline_mode_enabled']

@admin.register(VetSchedule)
class VetScheduleAdmin(admin.ModelAdmin):
    list_display = ['veterinarian', 'date', 'start_time', 'end_time', 'is_available']
    list_filter = ['is_available', 'date']
    search_fields = ['veterinarian__full_name', 'notes']

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

@admin.register(TreatmentRecord)
class TreatmentRecordAdmin(admin.ModelAdmin):
    list_display = ['medical_record', 'treatment', 'performed_by', 'performed_at']
    list_filter = ['performed_at']
    search_fields = ['treatment__name', 'notes', 'medical_record__pet__name']

@admin.register(OfflineChange)
class OfflineChangeAdmin(admin.ModelAdmin):
    list_display = ['change_type', 'model_type', 'created_by', 'created_at', 'is_synced']
    list_filter = ['change_type', 'model_type', 'is_synced', 'created_at']
    search_fields = ['created_by__username', 'data_json']