from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from clinic.models import Pet, Owner, Appointment, MedicalRecord, Prescription
from vet.models import Veterinarian, VetNotification
from ..models import VetSchedule, Treatment, TreatmentRecord, OfflineChange
from .serializers import (
    OwnerSerializer, PetSerializer, VeterinarianSerializer,
    AppointmentSerializer, MedicalRecordSerializer, PrescriptionSerializer,
    TreatmentSerializer, TreatmentRecordSerializer, VetScheduleSerializer,
    VetNotificationSerializer
)

import json


class IsVeterinarian(permissions.BasePermission):
    """
    Custom permission to only allow veterinarians to access the API.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'vet_profile')


class OwnerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing owners.
    Veterinarians can only view owners, not create/update/delete.
    """
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    permission_classes = [IsVeterinarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'email', 'phone']


class PetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing pets.
    Veterinarians can only view pets, not create/update/delete.
    """
    queryset = Pet.objects.select_related('owner').all()
    serializer_class = PetSerializer
    permission_classes = [IsVeterinarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'species', 'breed', 'owner__full_name']


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing appointments.
    Veterinarians can view, create, update, and delete appointments.
    """
    queryset = Appointment.objects.select_related('pet', 'pet__owner').all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsVeterinarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ['pet__name', 'pet__owner__full_name', 'reason', 'status']
    
    def perform_create(self, serializer):
        serializer.save()


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing medical records.
    Veterinarians can view, create, update, and delete medical records.
    """
    queryset = MedicalRecord.objects.select_related('pet').all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsVeterinarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ['pet__name', 'condition', 'treatment']


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing prescriptions.
    Veterinarians can view, create, update, and delete prescriptions.
    """
    queryset = Prescription.objects.select_related('pet').all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsVeterinarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ['pet__name', 'medication_name']


class TreatmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing treatments.
    Veterinarians can view, create, update, and delete treatments.
    """
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsVeterinarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class TreatmentRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing treatment records.
    Veterinarians can view, create, update, and delete treatment records.
    """
    queryset = TreatmentRecord.objects.select_related('medical_record', 'treatment', 'performed_by').all()
    serializer_class = TreatmentRecordSerializer
    permission_classes = [IsVeterinarian]
    
    def perform_create(self, serializer):
        # Set the performed_by field to the current veterinarian
        serializer.save(performed_by=self.request.user.vet_profile)


class VetScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing veterinarian schedules.
    Veterinarians can view all schedules but only update their own.
    """
    queryset = VetSchedule.objects.select_related('veterinarian').all()
    serializer_class = VetScheduleSerializer
    permission_classes = [IsVeterinarian]
    
    def get_queryset(self):
        # Filter by date range if provided
        queryset = super().get_queryset()
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    def perform_create(self, serializer):
        # Set the veterinarian field to the current veterinarian
        serializer.save(veterinarian=self.request.user.vet_profile)
    
    def perform_update(self, serializer):
        # Only allow veterinarians to update their own schedules
        if serializer.instance.veterinarian == self.request.user.vet_profile:
            serializer.save()
        else:
            raise permissions.PermissionDenied("You can only update your own schedule.")


class VetNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing notifications.
    Veterinarians can only view their own notifications.
    """
    serializer_class = VetNotificationSerializer
    permission_classes = [IsVeterinarian]
    
    def get_queryset(self):
        # Only return notifications for the current veterinarian
        return VetNotification.objects.filter(veterinarian=self.request.user.vet_profile)


@api_view(['POST'])
@permission_classes([IsVeterinarian])
def mark_notification_read(request, pk):
    """
    API endpoint for marking a notification as read.
    """
    notification = get_object_or_404(
        VetNotification, 
        pk=pk, 
        veterinarian=request.user.vet_profile
    )
    notification.is_read = True
    notification.save()
    
    return Response({'status': 'success'})


@api_view(['POST'])
@permission_classes([IsVeterinarian])
def mark_all_notifications_read(request):
    """
    API endpoint for marking all notifications as read.
    """
    VetNotification.objects.filter(
        veterinarian=request.user.vet_profile,
        is_read=False
    ).update(is_read=True)
    
    return Response({'status': 'success'})


@api_view(['POST'])
@permission_classes([IsVeterinarian])
def sync_offline_changes(request):
    """
    API endpoint for syncing offline changes.
    """
    try:
        changes = request.data.get('changes', [])
        results = []
        
        for change in changes:
            change_type = change.get('type')
            model_type = change.get('model')
            model_id = change.get('id')
            data = change.get('data', {})
            
            # Record the change
            offline_change = OfflineChange.objects.create(
                change_type=change_type,
                model_type=model_type,
                model_id=model_id,
                data_json=json.dumps(data),
                created_by=request.user,
                is_synced=False
            )
            
            # Process the change based on type and model
            result = {'status': 'pending', 'id': offline_change.id}
            
            try:
                if model_type == 'appointment':
                    if change_type == 'create':
                        serializer = AppointmentSerializer(data=data)
                        if serializer.is_valid():
                            serializer.save()
                            result = {'status': 'success', 'id': serializer.instance.id}
                        else:
                            result = {'status': 'error', 'errors': serializer.errors}
                    
                    elif change_type == 'update' and model_id:
                        appointment = get_object_or_404(Appointment, pk=model_id)
                        serializer = AppointmentSerializer(appointment, data=data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            result = {'status': 'success', 'id': serializer.instance.id}
                        else:
                            result = {'status': 'error', 'errors': serializer.errors}
                    
                    elif change_type == 'delete' and model_id:
                        appointment = get_object_or_404(Appointment, pk=model_id)
                        appointment.delete()
                        result = {'status': 'success', 'id': model_id}
                
                # Similar processing for other model types...
                
                # Mark the change as synced
                offline_change.is_synced = True
                offline_change.synced_at = timezone.now()
                offline_change.save()
            
            except Exception as e:
                result = {'status': 'error', 'message': str(e)}
            
            results.append(result)
        
        return Response({
            'status': 'success',
            'results': results,
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
