from __future__ import annotations

from typing import Optional
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction
from django.core.mail import send_mail

from clinic.models import Notification, Owner

import logging
logger = logging.getLogger('clinic')


def process_unsent_notifications(owner: Optional[Owner] = None, limit: int = 25) -> int:
    """
    Send emails for notifications that haven't been emailed yet.

    If an owner is provided, only process that owner's notifications; otherwise
    process globally up to the given limit.

    Returns the number of notifications enqueued for emailing.
    """
    qs = Notification.objects.filter(emailed=False)
    if owner is not None:
        qs = qs.filter(owner=owner)
    qs = qs.select_related('owner').order_by('created_at')[:limit]

    count = 0
    for notif in qs:
        o = notif.owner
        to_email = getattr(getattr(o, 'user', None), 'email', '') or (o.email or '')
        if not to_email:
            # Nothing to send to; mark as emailed to avoid repeated attempts
            Notification.objects.filter(pk=notif.pk, emailed=False).update(emailed=True)
            continue

        subject = f"{getattr(settings, 'BRAND_NAME', 'ePetCare')}: {notif.title}"
        ctx = {
            'title': notif.title,
            'message': notif.message,
            'owner': o,
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
            logger.info(f'Notification email sent to {to_email}')
        except Exception as e:
            # Skip marking emailed so it can be retried later
            logger.error(f'Failed to send notification email to {to_email}: {e}')
            continue
    return count
