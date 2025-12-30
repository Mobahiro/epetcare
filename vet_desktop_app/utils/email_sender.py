"""
Email sending utility for desktop app using SMTP or HTTP API
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger('epetcare')


def send_email_smtp(to_email: str, subject: str, body: str, html_body: str = None) -> bool:
    """
    Send email using SMTP (Gmail, SendGrid, or other provider)
    Returns True on success, False on failure
    """
    try:
        # Try to get config from config.json first
        smtp_host = None
        smtp_port = None
        smtp_user = None
        smtp_password = None
        from_email = None
        
        try:
            from utils.config import get_config
            config = get_config()
            if config and 'email' in config:
                email_config = config['email']
                smtp_host = email_config.get('smtp_host')
                smtp_port = email_config.get('smtp_port')
                smtp_user = email_config.get('smtp_user')
                smtp_password = email_config.get('smtp_password')
                from_email = email_config.get('from_email')
        except Exception as e:
            logger.debug(f"Could not load email config from config.json: {e}")
        
        # Fallback to environment variables
        smtp_host = smtp_host or os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
        smtp_port = smtp_port or int(os.environ.get('EMAIL_PORT', '587'))
        smtp_user = smtp_user or os.environ.get('EMAIL_HOST_USER', '')
        smtp_password = smtp_password or os.environ.get('EMAIL_HOST_PASSWORD', '')
        from_email = from_email or os.environ.get('DEFAULT_FROM_EMAIL', smtp_user)

        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured. Please set email configuration in config.json or environment variables.")
            return False

        logger.info(f"Attempting to send email to {to_email} via {smtp_host}:{smtp_port}")

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        # Attach text and HTML parts
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return True

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")
        return False


def send_email_via_api(to_email: str, subject: str, body: str) -> bool:
    """
    Send email by calling the backend API
    This uses the web app's email configuration (SendGrid, etc.)
    """
    try:
        import requests
        from utils.config import get_config
        
        config = get_config()
        if not config:
            logger.error("Config not loaded")
            return False
        
        api_url = config.get('api_url', 'http://localhost:8000')
        api_url = api_url.rstrip('/')
        
        # Call the backend API to send email
        response = requests.post(
            f"{api_url}/api/send-otp-email/",
            json={
                'to_email': to_email,
                'subject': subject,
                'message': body
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Email sent successfully via API to {to_email}")
            return True
        else:
            logger.error(f"API email send failed: {response.status_code} - {response.text}")
            return False
            
    except ImportError:
        logger.error("requests library not available")
        return False
    except Exception as e:
        logger.error(f"Failed to send email via API: {e}")
        return False


def send_otp_email(to_email: str, otp: str) -> bool:
    """
    Send OTP email (tries API first, falls back to SMTP)
    """
    subject = "ePetCare Password Reset OTP"
    body = f"""
Hello,

You have requested to reset your password for ePetCare Vet Desktop.

Your OTP code is: {otp}

This code is valid for 10 minutes.

If you did not request this, please ignore this email.

Best regards,
ePetCare Team
"""
    
    html_body = f"""
<html>
<body>
<p>Hello,</p>
<p>You have requested to reset your password for <strong>ePetCare Vet Desktop</strong>.</p>
<p>Your OTP code is: <strong style="font-size: 24px; color: #BB86FC;">{otp}</strong></p>
<p>This code is valid for <strong>10 minutes</strong>.</p>
<p>If you did not request this, please ignore this email.</p>
<br>
<p>Best regards,<br>ePetCare Team</p>
</body>
</html>
"""
    
    # Try API first (uses web app's configured email provider like SendGrid)
    if send_email_via_api(to_email, subject, body):
        return True
    
    # Fallback to SMTP
    logger.info("API email failed, trying SMTP...")
    return send_email_smtp(to_email, subject, body, html_body)
