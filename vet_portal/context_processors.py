"""
Context processors for vet_portal app
"""
from vet.models import VetNotification


def vet_notifications(request):
    """Add unread notification count to all templates"""
    context = {}
    
    if request.user.is_authenticated and hasattr(request.user, 'vet_profile'):
        try:
            context['unread_notifications_count'] = VetNotification.objects.filter(
                veterinarian=request.user.vet_profile,
                is_read=False
            ).count()
        except Exception:
            context['unread_notifications_count'] = 0
    else:
        context['unread_notifications_count'] = 0
    
    return context
