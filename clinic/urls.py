from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import PasswordResetRequestForm

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_us, name='about_us'),

    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.edit_profile, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),

    path('login/', auth_views.LoginView.as_view(template_name='clinic/login.html'), name='login'),
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

    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
]