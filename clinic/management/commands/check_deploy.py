from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Check critical environment variables required for deployment and email sending.'

    def handle(self, *args, **options):
        errors = []

        db = os.environ.get('DATABASE_URL') or getattr(settings, 'DATABASES', {}).get('default')
        if not db:
            errors.append('DATABASE_URL is not set or database configuration missing')

        provider = os.environ.get('EMAIL_HTTP_PROVIDER', '').strip().lower()
        if provider:
            if provider == 'sendgrid' and not os.environ.get('SENDGRID_API_KEY'):
                errors.append('EMAIL_HTTP_PROVIDER=sendgrid but SENDGRID_API_KEY is not set')
            if provider == 'resend' and not os.environ.get('RESEND_API_KEY'):
                errors.append('EMAIL_HTTP_PROVIDER=resend but RESEND_API_KEY is not set')
        else:
            # If no HTTP provider, check SMTP settings
            if not os.environ.get('EMAIL_HOST'):
                errors.append('EMAIL_HTTP_PROVIDER not set and EMAIL_HOST is missing for SMTP')

        default_from = os.environ.get('DEFAULT_FROM_EMAIL') or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not default_from:
            errors.append('DEFAULT_FROM_EMAIL is not configured')

        if errors:
            for e in errors:
                self.stdout.write(self.style.ERROR(e))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('Environment looks OK for deployment (basic checks passed).'))
