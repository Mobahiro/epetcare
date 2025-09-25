from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from clinic.models import Pet, Owner, Appointment, MedicalRecord, Prescription
from vet.models import Veterinarian, VetNotification
from ..models import VetSchedule, Treatment, TreatmentRecord, OfflineChange, VetPortalSettings
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


import os
import shutil
import tempfile
from django.http import FileResponse, HttpResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser


@api_view(['GET'])
@permission_classes([IsVeterinarian])
def database_sync(request):
    """
    API endpoint for getting database sync information.
    Returns metadata about the current database state.
    """
    try:
        from django.db import connection
        
        # Get the last sync time from settings
        last_sync = VetPortalSettings.objects.first()
        if not last_sync:
            last_sync = VetPortalSettings.objects.create()
        
        # Determine what tables have changed since last sync
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
        
        response_data = {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'last_sync': last_sync.last_sync_time.isoformat(),
            'tables': tables,
            'db_type': connection.vendor,
        }
        
        # For PostgreSQL, we need to handle this differently
        if connection.vendor == 'postgresql':
            response_data['sync_method'] = 'api'
            response_data['message'] = ('This database is using PostgreSQL. Direct file download '
                                        'is not available. Use the API endpoints instead.')
        else:
            response_data['sync_method'] = 'file'
        
        return Response(response_data)
    
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsVeterinarian])
def database_download(request):
    """
    API endpoint for downloading the database.
    For SQLite, it returns the actual database file.
    For PostgreSQL, it returns a dump of the database.
    """
    try:
        from django.db import connection
        
        # For PostgreSQL, we need to generate a dump
        if connection.vendor == 'postgresql':
            # This is just a placeholder - in a real scenario, you'd need to implement a proper 
            # PostgreSQL dump functionality using pg_dump or another solution
            return Response({
                'status': 'error',
                'message': 'Direct PostgreSQL database download not implemented. Use the API endpoints instead.'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        # For SQLite, we can send the actual file
        db_path = connection.settings_dict['NAME']
        
        if not os.path.exists(db_path):
            return Response({
                'status': 'error',
                'message': f'Database file not found at {db_path}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create a temporary copy to avoid locking the database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3') as temp:
            temp_path = temp.name
            shutil.copy2(db_path, temp_path)
        
        # Update the last sync time
        last_sync = VetPortalSettings.objects.first()
        if not last_sync:
            last_sync = VetPortalSettings.objects.create()
        else:
            last_sync.save()  # This updates the auto_now field
        
        # Return the database file
        response = FileResponse(
            open(temp_path, 'rb'),
            as_attachment=True,
            filename='epetcare_database.sqlite3'
        )
        
        # We'll delete the temp file after it's served
        response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        
        # Set a callback to delete the temp file
        def delete_temp_file(response):
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return response
        
        response.delete_temp_file = delete_temp_file
        
        return response
    
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsVeterinarian])
@parser_classes([MultiPartParser, FormParser])
def database_upload(request):
    """
    API endpoint for uploading database changes.
    For SQLite, it processes the changes from an uploaded file.
    For PostgreSQL, it applies changes through the ORM.
    """
    try:
        from django.db import connection
        
        # For PostgreSQL, we need to handle changes differently
        if connection.vendor == 'postgresql':
            # This would need to be a proper implementation that processes the changes
            # through the ORM instead of direct file uploads
            return Response({
                'status': 'error',
                'message': 'Direct PostgreSQL database upload not implemented. Use the API endpoints instead.'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        # For SQLite, we need to process the uploaded file
        if 'database' not in request.FILES:
            return Response({
                'status': 'error',
                'message': 'No database file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['database']
        
        # Create a temporary file to save the uploaded database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3') as temp:
            temp_path = temp.name
            for chunk in uploaded_file.chunks():
                temp.write(chunk)
        
        # Validate the uploaded file
        try:
            import sqlite3
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            
            if result != 'ok':
                os.unlink(temp_path)
                return Response({
                    'status': 'error',
                    'message': f'Uploaded database failed integrity check: {result}'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            os.unlink(temp_path)
            return Response({
                'status': 'error',
                'message': f'Uploaded file is not a valid SQLite database: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Here, we would process the changes from the uploaded database
        # This is a complex task and depends on your specific requirements
        # For simplicity, we'll just acknowledge the upload
        
        # Clean up
        os.unlink(temp_path)
        
        # Update the last sync time
        last_sync = VetPortalSettings.objects.first()
        if not last_sync:
            last_sync = VetPortalSettings.objects.create()
        else:
            last_sync.save()  # This updates the auto_now field
        
        return Response({
            'status': 'success',
            'message': 'Database upload acknowledged. In a real implementation, the changes would be processed.',
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
