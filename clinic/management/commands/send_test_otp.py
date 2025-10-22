import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.template.loader import render_to_string
from clinic.utils.emailing import send_mail_http


class Command(BaseCommand):
    help = "Send a test OTP email using the HTTP provider (SendGrid/Resend). Usage: manage.py send_test_otp you@example.com [--code 123456] [--from-email ...]"

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send the OTP to')
        parser.add_argument('--code', type=str, default='123456', help='OTP code to include in the email')
        parser.add_argument('--name', type=str, default=None, help='Optional recipient name for personalization')
        parser.add_argument('--from-email', dest='from_email', type=str, default=None, help='Override the From address for this test')

    def handle(self, *args, **options):
        recipient = options['recipient']
        code = options['code']
        subject = f"Your {getattr(settings, 'BRAND_NAME', 'ePetCare')} password reset code"
        ctx = {
            "code": code,
            "name": options.get('name'),
            "year": None,
            "BRAND_NAME": getattr(settings, 'BRAND_NAME', 'ePetCare'),
            "EMAIL_BRAND_LOGO_URL": getattr(settings, 'EMAIL_BRAND_LOGO_URL', ''),
        }
        message = render_to_string('clinic/auth/otp_email.txt', ctx)
        html_message = render_to_string('clinic/auth/otp_email.html', ctx)

        provider_env = os.environ.get('EMAIL_HTTP_PROVIDER', '').strip().lower() or '(not set)'
        provider_settings = getattr(settings, 'EMAIL_HTTP_PROVIDER', None) or '(not set)'
        effective_from = options.get('from_email') or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None) or 'no-reply@example.com'

        self.stdout.write(self.style.NOTICE(f'Provider (env): {provider_env}'))
        self.stdout.write(self.style.NOTICE(f'Provider (settings): {provider_settings}'))
        self.stdout.write(self.style.NOTICE(f'From (effective): {effective_from}'))

        ok = send_mail_http(subject, message, [recipient], from_email=options.get('from_email'), html_message=html_message)
        if ok:
            self.stdout.write(self.style.SUCCESS(f'Test OTP email sent to {recipient}'))
        else:
            raise CommandError('Failed to send OTP via HTTP provider. Check API key, provider, and verified From address.')
