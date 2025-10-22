from django.conf import settings


def branding(request):
    """Provide brand name and logo URL to all templates.

    Keys:
    - BRAND_NAME
    - EMAIL_BRAND_LOGO_URL
    """
    return {
        'BRAND_NAME': getattr(settings, 'BRAND_NAME', 'ePetCare'),
        'EMAIL_BRAND_LOGO_URL': getattr(settings, 'EMAIL_BRAND_LOGO_URL', ''),
    }
