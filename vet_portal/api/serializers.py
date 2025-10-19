from rest_framework import serializers
from clinic.models import Pet, Owner, Appointment, MedicalRecord, Prescription
from vet.models import Veterinarian, VetNotification
from ..models import VetSchedule, Treatment, TreatmentRecord


class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = ['id', 'full_name', 'email', 'phone', 'address', 'created_at']


class PetSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Pet
        fields = [
            'id', 'owner', 'owner_name', 'name', 'species', 'breed',
            'sex', 'birth_date', 'weight_kg', 'notes', 'image', 'image_url'
        ]

    def get_image_url(self, obj: Pet):  # type: ignore[name-defined]
        request = self.context.get('request') if hasattr(self, 'context') else None
        # Prefer the model's normalized property if available
        url = getattr(obj, 'image_url', None)
        if not url and getattr(obj, 'image', None):
            try:
                url = obj.image.url  # type: ignore[attr-defined]
            except Exception:
                url = None
        if not url:
            return None
        # Build absolute URI for desktop client consumption
        try:
            if request and not url.startswith(('http://', 'https://')):
                return request.build_absolute_uri(url)
        except Exception:
            pass
        return url


class VeterinarianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veterinarian
        fields = [
            'id', 'full_name', 'specialization', 'license_number',
            'phone', 'bio', 'created_at'
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    owner_name = serializers.CharField(source='pet.owner.full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'pet', 'pet_name', 'owner_name', 'date_time',
            'reason', 'notes', 'status'
        ]


class MedicalRecordSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'pet', 'pet_name', 'visit_date', 'condition',
            'treatment', 'vet_notes'
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'pet', 'pet_name', 'medication_name', 'dosage',
            'instructions', 'date_prescribed', 'duration_days', 'is_active'
        ]


class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = [
            'id', 'name', 'description', 'duration_minutes',
            'price', 'is_active'
        ]


class TreatmentRecordSerializer(serializers.ModelSerializer):
    treatment_name = serializers.CharField(source='treatment.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.full_name', read_only=True)

    class Meta:
        model = TreatmentRecord
        fields = [
            'id', 'medical_record', 'treatment', 'treatment_name',
            'notes', 'performed_by', 'performed_by_name', 'performed_at'
        ]


class VetScheduleSerializer(serializers.ModelSerializer):
    veterinarian_name = serializers.CharField(source='veterinarian.full_name', read_only=True)

    class Meta:
        model = VetSchedule
        fields = [
            'id', 'veterinarian', 'veterinarian_name', 'date',
            'start_time', 'end_time', 'is_available', 'notes'
        ]


class VetNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VetNotification
        fields = [
            'id', 'veterinarian', 'title', 'message',
            'is_read', 'created_at'
        ]
