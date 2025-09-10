from django.apps import AppConfig


class VetPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vet_portal'
    verbose_name = 'Veterinarian Portal'

    def ready(self):
        import vet_portal.signals  # Import signals