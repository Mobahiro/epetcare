from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os

urlpatterns = [
    path('', include('clinic.urls')),
    path('vet/', include('vet.urls')),
    path('vet_portal/', include('vet_portal.urls')),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),

    # Explicitly configure media serving in production
    path('media/<path:path>', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
