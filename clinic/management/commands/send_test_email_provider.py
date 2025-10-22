import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from clinic.utils.emailing import send_mail_http

class Command(BaseCommand):
    help = "Send a test email via the configured HTTP provider (SendGrid/Resend). Usage: manage.py send_test_email_provider you@example.com [--subject ...] [--message ...]"

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send the test message to')
        parser.add_argument('--subject', type=str, default='ePetCare: HTTP provider test', help='Email subject')
        parser.add_argument('--message', type=str, default='This is a test email via HTTP provider (no SMTP).', help='Email body')
        parser.add_argument('--from-email', dest='from_email', type=str, default=None, help='Override the From address for this test')

    def handle(self, *args, **options):
        recipient = options['recipient']
        subject = options['subject']
        message = options['message']

        # Provider is read from environment by the emailing utility; show both for clarity
        provider_env = os.environ.get('EMAIL_HTTP_PROVIDER', '').strip().lower() or '(not set)'
        provider_settings = getattr(settings, 'EMAIL_HTTP_PROVIDER', None) or '(not set)'

        # Determine effective from address (matches emailing.send_mail_http fallback logic)
        effective_from = options.get('from_email') or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None) or 'no-reply@example.com'

        self.stdout.write(self.style.NOTICE(f'Provider (env): {provider_env}'))
        self.stdout.write(self.style.NOTICE(f'Provider (settings): {provider_settings}'))
        self.stdout.write(self.style.NOTICE(f'From (settings DEFAULT_FROM_EMAIL): {getattr(settings, "DEFAULT_FROM_EMAIL", "")}'))
        self.stdout.write(self.style.NOTICE(f'From (effective): {effective_from}'))

        ok = send_mail_http(subject, message, [recipient], from_email=options.get('from_email'))
        if ok:
            self.stdout.write(self.style.SUCCESS(f'Test email sent to {recipient} via HTTP provider'))
        else:
            raise CommandError('Failed to send via HTTP provider. Check API key, provider, and from address.')
