from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings


class VetPortalMiddleware:
    """
    Middleware to restrict access to the vet portal to users with veterinarian role.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if the request is for the vet portal
        if request.path.startswith('/vet-portal/'):
            # Skip authentication check for login/logout pages
            if any(request.path.endswith(url) for url in ['/login/', '/logout/']):
                return self.get_response(request)
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.warning(request, "You need to log in to access the Veterinarian Portal.")
                return redirect(f"{reverse('vet_portal:login')}?next={request.path}")
            
            # Check if user is a veterinarian
            if not hasattr(request.user, 'vet_profile'):
                messages.error(
                    request, 
                    "Access denied. You need veterinarian privileges to access this portal."
                )
                return redirect('home')
        
        # Continue with the request
        return self.get_response(request)


class LocalNetworkMiddleware:
    """
    Middleware to restrict access to the vet portal to local network requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_ips = getattr(settings, 'VET_PORTAL_ALLOWED_IPS', ['127.0.0.1', '::1'])
    
    def __call__(self, request):
        # Check if the request is for the vet portal
        if request.path.startswith('/vet-portal/'):
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Check if IP is allowed
            if ip not in self.allowed_ips:
                # Check if we're in debug mode (allow all IPs in debug)
                if not settings.DEBUG:
                    messages.error(
                        request, 
                        "Access denied. The Veterinarian Portal can only be accessed from the local network."
                    )
                    return redirect('home')
        
        # Continue with the request
        return self.get_response(request)
