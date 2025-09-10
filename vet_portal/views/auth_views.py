from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from ..forms import VetLoginForm


class VetLoginView(LoginView):
    template_name = 'vet_portal/login.html'
    form_class = VetLoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('vet_portal:dashboard')


class VetLogoutView(LogoutView):
    next_page = reverse_lazy('vet_portal:login')
