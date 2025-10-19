from django.urls import path, include
from django.conf import settings
from . import views
from .deploy_hooks import deploy_hook
from .views.debug_views import media_debug, media_upload_form

app_name = 'vet_portal'

urlpatterns = [
    # Deploy hook for Render
    path('deploy/', deploy_hook, name='deploy_hook'),
    # Authentication
    path('login/', views.VetLoginView.as_view(), name='login'),
    path('logout/', views.VetLogoutView.as_view(), name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Patients
    path('patients/', views.PatientListView.as_view(), name='patient_list'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient_detail'),
    # Medical Records
    path('patients/<int:pet_id>/records/new/', views.medical_record_create, name='medical_record_create'),
    path('records/<int:pk>/edit/', views.medical_record_update, name='medical_record_update'),
    path('records/<int:pk>/delete/', views.medical_record_delete, name='medical_record_delete'),
    # Prescriptions
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