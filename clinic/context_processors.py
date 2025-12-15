from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from .models import Notification


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


def notifications(request):
    """Provide global notifications info to all templates.

    Keys:
    - GLOBAL_NOTIFICATIONS_UNREAD_COUNT: integer count of unread notifications for the logged-in owner
    - GLOBAL_HAS_NOTIFICATIONS: convenience boolean
    """
    user = getattr(request, 'user', None)
    if not user or isinstance(user, AnonymousUser):
        return {
            'GLOBAL_NOTIFICATIONS_UNREAD_COUNT': 0,
            'GLOBAL_HAS_NOTIFICATIONS': False,
        }
    owner = getattr(user, 'owner_profile', None)
    if not owner:
        return {
            'GLOBAL_NOTIFICATIONS_UNREAD_COUNT': 0,
            'GLOBAL_HAS_NOTIFICATIONS': False,
        }
    try:
        unread_count = Notification.objects.filter(owner=owner, is_read=False).count()
    except Exception:
        unread_count = 0
    return {
        'GLOBAL_NOTIFICATIONS_UNREAD_COUNT': unread_count,
        'GLOBAL_HAS_NOTIFICATIONS': bool(unread_count),
    }
