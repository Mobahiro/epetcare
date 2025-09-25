from django.urls import path, include
from . import views
from .deploy_hooks import deploy_hook

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
    
    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    
    # API endpoints
    path('api/', include('vet_portal.api.urls')),
]