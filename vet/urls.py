from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from . import views

app_name = 'vet'

# Redirect vet login to unified login
def vet_login_redirect(request):
    from django.shortcuts import redirect
    return redirect('unified_login')

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.vet_profile, name='profile'),
    path('profile/update-field/', views.profile_update_field, name='profile_update_field'),
    path('profile/request-field-otp/', views.profile_request_field_otp, name='profile_request_field_otp'),
    path('profile/verify-field-otp/', views.profile_verify_field_otp, name='profile_verify_field_otp'),
    path('profile/password/request-otp/', views.change_password_request_otp, name='profile_request_password_otp'),
    path('profile/password/verify-otp/', views.change_password_verify_otp, name='profile_verify_password_otp'),
    path('profile/password/set-new/', views.change_password_set_new, name='profile_set_new_password'),
    path('patients/', views.patients, name='patients'),
    path('appointments/', views.appointments, name='appointments'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Redirect to unified login
    path('login/', vet_login_redirect, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
