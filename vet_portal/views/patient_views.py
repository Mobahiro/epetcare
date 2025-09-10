from django.views.generic import ListView, DetailView
from django.db.models import Q

from clinic.models import Pet, MedicalRecord, Appointment, Prescription
from ..mixins import VeterinarianRequiredMixin


class PatientListView(VeterinarianRequiredMixin, ListView):
    model = Pet
    template_name = 'vet_portal/patients/list.html'
    context_object_name = 'patients'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Pet.objects.select_related('owner').all()
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(owner__full_name__icontains=search_query) |
                Q(species__icontains=search_query) |
                Q(breed__icontains=search_query)
            )
        
        return queryset


class PatientDetailView(VeterinarianRequiredMixin, DetailView):
    model = Pet
    template_name = 'vet_portal/patients/detail.html'
    context_object_name = 'patient'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object
        
        # Get related data
        context['medical_records'] = MedicalRecord.objects.filter(
            pet=patient
        ).order_by('-visit_date')
        
        context['appointments'] = Appointment.objects.filter(
            pet=patient
        ).order_by('-date_time')
        
        context['prescriptions'] = Prescription.objects.filter(
            pet=patient
        ).order_by('-date_prescribed')
        
        return context