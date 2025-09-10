from django.contrib.auth.mixins import UserPassesTestMixin


def is_veterinarian(user):
    """Helper function to check if user is a veterinarian"""
    return user.is_authenticated and hasattr(user, 'vet_profile')


class VeterinarianRequiredMixin(UserPassesTestMixin):
    """Mixin for class-based views to restrict access to veterinarians"""
    def test_func(self):
        return is_veterinarian(self.request.user)