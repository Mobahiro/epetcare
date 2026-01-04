from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import superadmin_views

router = DefaultRouter()
router.register(r'owners', views.OwnerViewSet, basename='owner')
router.register(r'pets', views.PetViewSet, basename='pet')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'medical-records', views.MedicalRecordViewSet, basename='medicalrecord')
router.register(r'prescriptions', views.PrescriptionViewSet, basename='prescription')
router.register(r'treatments', views.TreatmentViewSet, basename='treatment')
router.register(r'treatment-records', views.TreatmentRecordViewSet, basename='treatmentrecord')
router.register(r'vet-schedules', views.VetScheduleViewSet, basename='vetschedule')
router.register(r'vet-notifications', views.VetNotificationViewSet, basename='vet-notification')

urlpatterns = [
    # Superadmin API endpoints (for mobile app)
    path('superadmin/login/', superadmin_views.superadmin_login, name='superadmin-login'),
    path('superadmin/stats/', superadmin_views.get_dashboard_stats, name='superadmin-stats'),
    path('superadmin/veterinarians/', superadmin_views.list_veterinarians, name='superadmin-vets'),
    path('superadmin/veterinarians/<int:vet_id>/approve/', superadmin_views.approve_veterinarian, name='superadmin-approve-vet'),
    path('superadmin/veterinarians/<int:vet_id>/reject/', superadmin_views.reject_veterinarian, name='superadmin-reject-vet'),
    path('superadmin/veterinarians/<int:vet_id>/delete/', superadmin_views.delete_veterinarian, name='superadmin-delete-vet'),
    path('superadmin/owners/', superadmin_views.list_owners, name='superadmin-owners'),
    path('superadmin/owners/<int:owner_id>/delete/', superadmin_views.delete_owner, name='superadmin-delete-owner'),
    path('superadmin/pets/', superadmin_views.list_pets, name='superadmin-pets'),
    path('superadmin/superadmins/', superadmin_views.list_superadmins, name='superadmin-list'),
    path('superadmin/superadmins/create/', superadmin_views.create_superadmin, name='superadmin-create'),
    path('superadmin/superadmins/<int:superadmin_id>/delete/', superadmin_views.delete_superadmin, name='superadmin-delete'),
    path('superadmin/users/<int:user_id>/reset-password/', superadmin_views.reset_user_password, name='superadmin-reset-password'),
    path('superadmin/users/<int:user_id>/toggle-status/', superadmin_views.toggle_user_status, name='superadmin-toggle-status'),

    # Manual endpoints BEFORE router to avoid conflicts
    path('notification/<int:pk>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('notifications/count/', views.notification_count, name='notification-count'),
    path('sync/offline-changes/', views.sync_offline_changes, name='sync-offline-changes'),

    # Router-based viewsets
    path('', include(router.urls)),

    # Database synchronization endpoints
    path('database/sync/', views.database_sync, name='database-sync'),
    path('database/download/', views.database_download, name='database-download'),
    path('database/upload/', views.database_upload, name='database-upload'),
    # Media check
    path('media/check/', views.media_check, name='media-check'),
    path('media/upload/', views.media_upload, name='media-upload'),
    # Email sending (for desktop app OTP)
    path('send-otp-email/', views.send_otp_email, name='send-otp-email'),
]