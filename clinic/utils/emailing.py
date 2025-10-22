from __future__ import annotations

import threading
import logging
from typing import List, Optional
import os

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore

from django.core.mail import send_mail, get_connection, EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger('clinic')


def _send(subject: str, message: str, recipient_list: List[str], from_email: Optional[str] = None, html_message: Optional[str] = None) -> None:
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
                        used_http = _send_via_sendgrid(api_key, subject, message, recipient_list, from_addr, html_message=html_message)
                    else:
                        logger.error('SENDGRID_API_KEY missing while EMAIL_HTTP_PROVIDER=sendgrid')
                elif provider == 'resend':
                    api_key = os.environ.get('RESEND_API_KEY', '').strip()
                    if api_key:
                        used_http = _send_via_resend(api_key, subject, message, recipient_list, from_addr, html_message=html_message)
                    else:
                        logger.error('RESEND_API_KEY missing while EMAIL_HTTP_PROVIDER=resend')
            except Exception as e:
                logger.error('HTTP email provider send failed: %s', e)

        if used_http:
            logger.info('Email sent via %s to %s: %s', provider, ','.join(recipient_list), subject)
            return

        # Use an explicit connection to honor settings and timeouts
        with get_connection() as connection:
            from_addr = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None)
            if html_message:
                msg = EmailMultiAlternatives(subject, message or '', from_addr, recipient_list, connection=connection)
                msg.attach_alternative(html_message, "text/html")
                msg.send(fail_silently=False)
            else:
                send_mail(
                    subject,
                    message,
                    from_addr,
                    recipient_list,
                    fail_silently=False,
                    connection=connection,
                )
        logger.info('Email sent to %s: %s', ','.join(recipient_list), subject)
    except Exception as e:
        # Log but never raise; this should never crash the request
        logger.error('Email send failed: %s', e)


def send_mail_async_safe(subject: str, message: str, recipient_list: List[str], from_email: Optional[str] = None, html_message: Optional[str] = None) -> None:
    """
    Dispatch email send on a daemon thread to avoid blocking the request.
    The thread is fire-and-forget; failures are logged by _send.
    """
    t = threading.Thread(target=_send, args=(subject, message, recipient_list, from_email, html_message), daemon=True)
    t.start()


def send_mail_http(subject: str, message: str, recipient_list: List[str], from_email: Optional[str] = None, html_message: Optional[str] = None) -> bool:
    """
    Sends email via configured HTTP provider synchronously.
    Returns True on success, False otherwise. Does not attempt SMTP.
    """
    provider = os.environ.get('EMAIL_HTTP_PROVIDER', '').strip().lower()
    if not provider:
        logger.error('EMAIL_HTTP_PROVIDER not set; cannot send via HTTP provider')
        return False
    from_addr = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None) or 'no-reply@example.com'
    try:
        if provider == 'sendgrid':
            api_key = os.environ.get('SENDGRID_API_KEY', '').strip()
            if not api_key:
                logger.error('SENDGRID_API_KEY missing; cannot send via SendGrid')
                return False
            return _send_via_sendgrid(api_key, subject, message, recipient_list, from_addr, html_message=html_message)
        elif provider == 'resend':
            api_key = os.environ.get('RESEND_API_KEY', '').strip()
            if not api_key:
                logger.error('RESEND_API_KEY missing; cannot send via Resend')
                return False
            return _send_via_resend(api_key, subject, message, recipient_list, from_addr, html_message=html_message)
        else:
            logger.error('Unknown EMAIL_HTTP_PROVIDER=%s', provider)
            return False
    except Exception as e:
        logger.error('HTTP provider send failed: %s', e)
        return False


def _send_via_sendgrid(api_key: str, subject: str, message: str, recipient_list: List[str], from_email: Optional[str], html_message: Optional[str] = None) -> bool:
    if requests is None:
        return False
    from email.utils import parseaddr
    url = 'https://api.sendgrid.com/v3/mail/send'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    # Ensure we pass a pure email address to SendGrid
    display_name, pure_email = parseaddr(from_email or 'no-reply@example.com')
    if not display_name:
        display_name = 'ePetCare'
    data = {
        'personalizations': [{'to': [{'email': r} for r in recipient_list]}],
        'from': {'email': pure_email or 'no-reply@example.com', 'name': display_name},
        'subject': subject,
        # Provide both text and html when available (order matters: some clients prefer the last part)
        'content': (
            [{'type': 'text/plain', 'value': message}]
            + ([{'type': 'text/html', 'value': html_message}] if html_message else [])
        ),
        # Mark as transactional and disable tracking to avoid link rewriting which can trigger spam filters
        'categories': ['transactional'],
        'tracking_settings': {
            'click_tracking': {'enable': False, 'enable_text': False},
            'open_tracking': {'enable': False},
        },
    }
    resp = requests.post(url, json=data, headers=headers, timeout=15)
    if resp.status_code in (200, 202):
        return True
    logger.error('SendGrid error %s: %s', resp.status_code, resp.text)
    return False


def _send_via_resend(api_key: str, subject: str, message: str, recipient_list: List[str], from_email: Optional[str], html_message: Optional[str] = None) -> bool:
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
    }
    if html_message:
        data['html'] = html_message
        if message:
            data['text'] = message
    else:
        data['text'] = message
    resp = requests.post(url, json=data, headers=headers, timeout=15)
    if 200 <= resp.status_code < 300:
        return True
    logger.error('Resend error %s: %s', resp.status_code, resp.text)
    return False
