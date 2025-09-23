from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('login/', auth_views.LoginView.as_view(template_name='clinic/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('owners/', views.owner_list, name='owner_list'),
    path('owners/new/', views.owner_create, name='owner_create'),
    path('owners/<int:pk>/', views.owner_detail, name='owner_detail'),

    path('pets/', views.pet_list, name='pet_list'),
    path('pets/new/', views.pet_create, name='pet_create'),
    path('pets/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('pets/<int:pk>/delete/', views.pet_delete, name='pet_delete'),

    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
]