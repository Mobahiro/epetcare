"""
Email utilities for safe, non-blocking sends in request/response cycle.
We use a short-lived background thread to avoid blocking Gunicorn worker
when SMTP servers are slow or unreachable. Errors are logged, not raised.

Supports two transport modes:
- SMTP via Django email backend (default)
- HTTP API providers (optional) when configured via env:
    - EMAIL_HTTP_PROVIDER=sendgrid and SENDGRID_API_KEY=...
    - EMAIL_HTTP_PROVIDER=resend and RESEND_API_KEY=...

If an HTTP provider is configured, we try it first; on failure, we fall back
to SMTP to maximize chances of delivery.
"""
from __future__ import annotations

import threading
import logging
from typing import List, Optional
import os

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore

from django.core.mail import send_mail, get_connection
from django.conf import settings

logger = logging.getLogger('clinic')


def _send(subject: str, message: str, recipient_list: List[str], from_email: Optional[str] = None) -> None:
    try:
        # Try HTTP provider first if configured
        provider = os.environ.get('EMAIL_HTTP_PROVIDER', '').strip().lower()
        used_http = False
        if provider and requests is None:
            logger.error('EMAIL_HTTP_PROVIDER=%s but requests is not installed', provider)
        if provider and requests is not None:
            from_addr = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None)
            try:
                if provider == 'sendgrid':
                    api_key = os.environ.get('SENDGRID_API_KEY', '').strip()
                    if api_key:
                        used_http = _send_via_sendgrid(api_key, subject, message, recipient_list, from_addr)
                    else:
                        logger.error('SENDGRID_API_KEY missing while EMAIL_HTTP_PROVIDER=sendgrid')
                elif provider == 'resend':
                    api_key = os.environ.get('RESEND_API_KEY', '').strip()
                    if api_key:
                        used_http = _send_via_resend(api_key, subject, message, recipient_list, from_addr)
                    else:
                        logger.error('RESEND_API_KEY missing while EMAIL_HTTP_PROVIDER=resend')
            except Exception as e:
                logger.error('HTTP email provider send failed: %s', e)

        if used_http:
            logger.info('Email sent via %s to %s: %s', provider, ','.join(recipient_list), subject)
            return

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


def _send_via_sendgrid(api_key: str, subject: str, message: str, recipient_list: List[str], from_email: Optional[str]) -> bool:
    if requests is None:
        return False
    url = 'https://api.sendgrid.com/v3/mail/send'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        'personalizations': [{'to': [{'email': r} for r in recipient_list]}],
        'from': {'email': from_email or 'no-reply@example.com', 'name': 'ePetCare'},
        'subject': subject,
        'content': [{'type': 'text/plain', 'value': message}],
    }
    resp = requests.post(url, json=data, headers=headers, timeout=15)
    if resp.status_code in (200, 202):
        return True
    logger.error('SendGrid error %s: %s', resp.status_code, resp.text)
    return False


def _send_via_resend(api_key: str, subject: str, message: str, recipient_list: List[str], from_email: Optional[str]) -> bool:
    if requests is None:
        return False
    url = 'https://api.resend.com/emails'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        'from': from_email or 'ePetCare <no-reply@epetcare.onrender.com>',
        'to': recipient_list,
        'subject': subject,
        'text': message,
    }
    resp = requests.post(url, json=data, headers=headers, timeout=15)
    if 200 <= resp.status_code < 300:
        return True
    logger.error('Resend error %s: %s', resp.status_code, resp.text)
    return False
