from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from clinic.models import Notification

class Command(BaseCommand):
    help = "Send email for notifications that haven't been emailed yet"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100, help='Max notifications to process')

    def handle(self, *args, **options):
        limit = options['limit']
        qs = Notification.objects.filter(emailed=False).select_related('owner').order_by('created_at')[:limit]
        count = 0
        for notif in qs:
            owner = notif.owner
            to_email = getattr(getattr(owner, 'user', None), 'email', '') or (owner.email or '')
            if not to_email:
                continue
            subject = f"{getattr(settings, 'BRAND_NAME', 'ePetCare')}: {notif.title}"
            ctx = {
                'title': notif.title,
                'message': notif.message,
                'owner': owner,
                'created_at': notif.created_at,
                'BRAND_NAME': getattr(settings, 'BRAND_NAME', 'ePetCare'),
                'EMAIL_BRAND_LOGO_URL': getattr(settings, 'EMAIL_BRAND_LOGO_URL', ''),
            }
            try:
                text_body = render_to_string('clinic/notifications/email_notification.txt', ctx)
            except Exception:
                text_body = f"{notif.title}\n\n{notif.message}\n\n— {getattr(settings, 'BRAND_NAME', 'ePetCare')}"
            try:
                html_body = render_to_string('clinic/notifications/email_notification.html', ctx)
            except Exception:
                html_body = None
            try:
                send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email], html_message=html_body, fail_silently=False)
                Notification.objects.filter(pk=notif.pk, emailed=False).update(emailed=True)
                count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send to {to_email}: {e}"))
                continue
        self.stdout.write(self.style.SUCCESS(f"Processed {count} notifications"))
