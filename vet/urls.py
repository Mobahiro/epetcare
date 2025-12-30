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
    path('patients/', views.patients, name='patients'),
    path('appointments/', views.appointments, name='appointments'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Redirect to unified login
    path('login/', vet_login_redirect, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
