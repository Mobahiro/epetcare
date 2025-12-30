from django.urls import path, include
from django.conf import settings
from . import views
from .deploy_hooks import deploy_hook
from .views.debug_views import media_debug, media_upload_form
from .views.auth_views import register

app_name = 'vet_portal'

urlpatterns = [
    # Deploy hook for Render
    path('deploy/', deploy_hook, name='deploy_hook'),
    # Authentication
    path('login/', views.VetLoginView.as_view(), name='login'),
    path('logout/', views.vet_logout_view, name='logout'),
    path('register/', register, name='register'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Patients
    path('patients/', views.PatientListView.as_view(), name='patient_list'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient_detail'),
    
    # Appointments
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/complete/', views.appointment_complete, name='appointment_complete'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    
    # Prescriptions
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    
    # Schedule
    path('schedule/', views.schedule_list, name='schedule_list'),
    
    # Medical Records
    path('records/', views.medical_record_list, name='medical_record_list'),
    path('records/<int:pk>/', views.medical_record_detail, name='medical_record_detail'),
    
    # Notifications
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Manifest for PWA
    path('manifest.json', views.manifest, name='manifest'),
    
    # Medical Records (create/edit/delete)
    path('patients/<int:pet_id>/records/new/', views.medical_record_create, name='medical_record_create'),
    path('records/<int:pk>/edit/', views.medical_record_update, name='medical_record_update'),
    path('records/<int:pk>/delete/', views.medical_record_delete, name='medical_record_delete'),
    
    # Prescriptions (create/edit/delete)
    path('patients/<int:pet_id>/prescriptions/new/', views.prescription_create, name='prescription_create'),
    path('prescriptions/<int:pk>/edit/', views.prescription_update, name='prescription_update'),
    path('prescriptions/<int:pk>/delete/', views.prescription_delete, name='prescription_delete'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # API endpoints
    path('api/', include('vet_portal.api.urls')),

    # Debug endpoints
    path('debug/media/', media_debug, name='media_debug'),
    path('tools/upload-media/', media_upload_form, name='media_upload_form'),
]