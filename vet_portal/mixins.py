from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test


def is_veterinarian(user):
    """Return True if the user is an authenticated Veterinarian.

    We check against the `vet.Veterinarian` model instead of relying on a
    dynamic attribute. This keeps behavior consistent across both function-
    based and class-based views.
    """
    if not getattr(user, 'is_authenticated', False):
        return False
    try:
        from vet.models import Veterinarian  # local import to avoid app registry issues
        return Veterinarian.objects.filter(user=user).exists()
    except Exception:
        # If model import fails during migrations/startup, deny access by default
        return False


# Decorator for function-based views
vet_required = user_passes_test(is_veterinarian)


class VeterinarianRequiredMixin(UserPassesTestMixin):
    """Mixin for class-based views to restrict access to veterinarians"""
    def test_func(self):
        return is_veterinarian(self.request.user)