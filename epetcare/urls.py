"""
URL configuration for epetcare project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clinic.urls')),
    path('vet/', include('vet.urls')),
]