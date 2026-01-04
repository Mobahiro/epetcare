from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .models import Notification


# Branch keywords for vet registration
VET_BRANCH_KEYWORDS = ['taguig@vet', 'pasig@vet', 'makati@vet']


@require_http_methods(["GET"])
def check_user_type(request):
    """Check if a username belongs to a veterinarian account"""
    username_raw = request.GET.get('username', '').strip()
    username = username_raw.lower()

    if not username:
        return JsonResponse({'is_vet': False})

    # Treat accounts as veterinarians when the provided identifier
    # matches any branch keyword pattern (case-insensitive)
    if any(username.endswith(keyword) for keyword in VET_BRANCH_KEYWORDS):
        return JsonResponse({'is_vet': True})

    # Fallback: do not consider other usernames as vets
    return JsonResponse({'is_vet': False})


@require_http_methods(["GET"])
def branch_vet_counts(request):
    """Return count of approved veterinarians per branch"""
    from vet.models import Veterinarian
    
    counts = Veterinarian.get_branch_vet_counts()
    return JsonResponse(counts)


@login_required
@require_http_methods(["GET"])
def notification_count(request):
    """Return unread notification count for logged-in pet owner"""
    try:
        owner = request.user.owner_profile
        count = Notification.objects.filter(owner=owner, is_read=False).count()
        return JsonResponse({'unread_count': count})
    except Exception:
        return JsonResponse({'unread_count': 0})
