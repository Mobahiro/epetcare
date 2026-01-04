from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .auth_views import unified_login
from .forms import PasswordResetRequestForm
from .api_views import check_user_type, branch_vet_counts, notification_count

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_us, name='about_us'),

    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API endpoints
    path('check-user-type/', check_user_type, name='check_user_type'),
    path('api/branch-vet-counts/', branch_vet_counts, name='branch_vet_counts'),
    path('api/notification-count/', notification_count, name='notification_count'),
    path('profile/', views.edit_profile, name='profile'),
    path('profile/update-field/', views.profile_update_field, name='profile_update_field'),
    path('profile/request-field-otp/', views.profile_request_field_otp, name='profile_request_field_otp'),
    path('profile/verify-field-otp/', views.profile_verify_field_otp, name='profile_verify_field_otp'),
    path('profile/password/request-otp/', views.change_password_request_otp, name='profile_request_password_otp'),
    path('profile/password/verify-otp/', views.change_password_verify_otp, name='profile_verify_password_otp'),
    path('profile/password/set-new/', views.change_password_set_new, name='profile_set_new_password'),

    # Unified login for both pet owners and vets
    path('login/', unified_login, name='unified_login'),
    path('auth/login/', unified_login, name='login'),  # Keep 'login' name for compatibility
    path('logout/', views.logout_view, name='logout'),

    # OTP first password reset flow
    path('password-reset/code/', views.password_reset_request_otp, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_verify_otp, name='password_reset_verify'),
    path('password-reset/new/', views.password_reset_set_new, name='password_reset_set_new'),

    # Password reset (forgot password)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='clinic/auth/password_reset_form.html',
        form_class=PasswordResetRequestForm,
        email_template_name='clinic/auth/password_reset_email.html',
        subject_template_name='clinic/auth/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='clinic/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='clinic/auth/password_reset_confirm.html',
        success_url='/reset/complete/'
    ), name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='clinic/auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('owners/', views.owner_list, name='owner_list'),
    path('owners/new/', views.owner_create, name='owner_create'),
    path('owners/<int:pk>/', views.owner_detail, name='owner_detail'),

    path('pets/', views.pet_list, name='pet_list'),
    path('pets/new/', views.pet_create, name='pet_create'),
    path('pets/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('pets/<int:pk>/edit/', views.pet_edit, name='pet_edit'),
    path('pets/<int:pk>/delete/', views.pet_delete, name='pet_delete'),

    path('medical-records/<int:pk>/delete/', views.medical_record_delete, name='medical_record_delete'),

    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/reschedule/', views.appointment_reschedule, name='appointment_reschedule'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
]