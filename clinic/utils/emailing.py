"""
Email utilities for safe, non-blocking sends in request/response cycle.
We use a short-lived background thread to avoid blocking Gunicorn worker
when SMTP servers are slow or unreachable. Errors are logged, not raised.
"""
from __future__ import annotations

import threading
import logging
from typing import List, Optional

from django.core.mail import send_mail, get_connection
from django.conf import settings

logger = logging.getLogger('clinic')


def _send(subject: str, message: str, recipient_list: List[str], from_email: Optional[str] = None) -> None:
    try:
        # Use an explicit connection to honor settings and timeouts
        with get_connection() as connection:
            send_mail(
                subject,
                message,
                from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None),
                recipient_list,
                fail_silently=False,
                connection=connection,
            )
        logger.info('Email sent to %s: %s', ','.join(recipient_list), subject)
    except Exception as e:
        # Log but never raise; this should never crash the request
        logger.error('Email send failed: %s', e)


def send_mail_async_safe(subject: str, message: str, recipient_list: List[str], from_email: Optional[str] = None) -> None:
    """
    Dispatch email send on a daemon thread to avoid blocking the request.
    The thread is fire-and-forget; failures are logged by _send.
    """
    t = threading.Thread(target=_send, args=(subject, message, recipient_list, from_email), daemon=True)
    t.start()
