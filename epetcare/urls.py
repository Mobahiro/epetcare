"""
URL configuration for epetcare project.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('clinic.urls')),
    path('vet/', include('vet.urls')),
]