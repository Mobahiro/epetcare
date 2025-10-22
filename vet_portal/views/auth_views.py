from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from ..forms import VetLoginForm, VetRegistrationForm
from django.shortcuts import redirect


class VetLoginView(LoginView):
    template_name = 'vet_portal/login.html'
    form_class = VetLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('vet_portal:dashboard')


class VetLogoutView(LogoutView):
    next_page = reverse_lazy('vet_portal:login')


def register(request):
    if request.method == 'POST':
        form = VetRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('vet_portal:login')
    else:
        form = VetRegistrationForm()
    return __import__('django').shortcuts.render(request, 'vet_portal/register.html', {'form': form})
