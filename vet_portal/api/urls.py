from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'owners', views.OwnerViewSet, basename='owner')
router.register(r'pets', views.PetViewSet, basename='pet')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'medical-records', views.MedicalRecordViewSet, basename='medicalrecord')
router.register(r'prescriptions', views.PrescriptionViewSet, basename='prescription')
router.register(r'treatments', views.TreatmentViewSet, basename='treatment')
router.register(r'treatment-records', views.TreatmentRecordViewSet, basename='treatmentrecord')
router.register(r'vet-schedules', views.VetScheduleViewSet, basename='vetschedule')
router.register(r'notifications', views.VetNotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('notification/<int:pk>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('sync/offline-changes/', views.sync_offline_changes, name='sync-offline-changes'),

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