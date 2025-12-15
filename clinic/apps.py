from django.apps import AppConfig


class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic'

    def ready(self):
        # Import signal handlers
        import logging
        logger = logging.getLogger('clinic')
        logger.info('[APP] ClinicConfig.ready() called - importing signals')
        from . import signals  # noqa: F401
        logger.info('[APP] Signals imported successfully')
