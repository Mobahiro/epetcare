from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('clinic.urls')),
    path('vet/', include('vet.urls')),
    path('vet_portal/', include('vet_portal.urls')),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
]

# Serve media files in all environments
# This is for development - WhiteNoise handles static files in production
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, media files need special handling
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
