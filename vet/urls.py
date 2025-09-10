from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'vet'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patients/', views.patients, name='patients'),
    path('appointments/', views.appointments, name='appointments'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    path('login/', auth_views.LoginView.as_view(
        template_name='vet/login.html',
        redirect_field_name='next',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),
]
