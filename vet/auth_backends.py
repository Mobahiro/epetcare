"""
Custom authentication backend for veterinarians.
This backend ensures that only approved vets can login.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class VetApprovalBackend(ModelBackend):
    """
    Custom authentication backend that checks if a veterinarian
    is approved before allowing login.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First, use the standard authentication
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user is None:
            return None
        
        # Check if user has a vet profile
        if hasattr(user, 'vet_profile'):
            vet = user.vet_profile
            
            # Only allow login if vet is approved
            if not vet.is_approved:
                return None
        
        return user
