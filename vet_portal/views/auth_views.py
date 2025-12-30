from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from ..forms import VetLoginForm, VetRegistrationForm
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages


class VetLoginView(LoginView):
    template_name = 'vet_portal/login.html'
    form_class = VetLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('vet_portal:dashboard')


def vet_logout_view(request):
    """Simple logout view that redirects to homepage"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


def register(request):
    if request.method == 'POST':
        form = VetRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('vet_portal:login')
    else:
        form = VetRegistrationForm()
    return __import__('django').shortcuts.render(request, 'vet_portal/register.html', {'form': form})
