from django.apps import AppConfig


class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic'

    def ready(self):
        # Import signal handlers
        from . import signals  # noqa: F401
