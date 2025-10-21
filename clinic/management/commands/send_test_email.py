from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, get_connection
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email to verify SMTP configuration. Usage: manage.py send_test_email you@example.com [--subject ...] [--message ...]"

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send the test message to')
        parser.add_argument('--subject', type=str, default='ePetCare: SMTP test', help='Email subject')
        parser.add_argument('--message', type=str, default='This is a test email from ePetCare.', help='Email body')

    def handle(self, *args, **options):
        recipient = options['recipient']
        subject = options['subject']
        message = options['message']

        self.stdout.write(self.style.NOTICE('Attempting to send test email...'))
        self.stdout.write(f"Backend: {getattr(settings, 'EMAIL_BACKEND', '')}")
        self.stdout.write(f"Host: {getattr(settings, 'EMAIL_HOST', '')}")
        self.stdout.write(f"Port: {getattr(settings, 'EMAIL_PORT', '')}")
        self.stdout.write(f"TLS: {getattr(settings, 'EMAIL_USE_TLS', '')} | SSL: {getattr(settings, 'EMAIL_USE_SSL', '')}")
        self.stdout.write(f"From: {getattr(settings, 'DEFAULT_FROM_EMAIL', '')}")

        try:
            # Ensure connection can be established (useful for early error)
            with get_connection() as connection:
                send_mail(
                    subject,
                    message,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None),
                    [recipient],
                    fail_silently=False,
                    connection=connection,
                )
            self.stdout.write(self.style.SUCCESS(f"Test email sent to {recipient}"))
        except Exception as e:
            raise CommandError(f"Failed to send test email: {e}")
