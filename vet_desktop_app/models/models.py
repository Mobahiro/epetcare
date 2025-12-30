"""
Data models for the ePetCare Vet Desktop application.
These models mirror the Django models in the web application.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class AppointmentStatus(Enum):
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class PetSpecies(Enum):
    DOG = 'dog'
    CAT = 'cat'
    BIRD = 'bird'
    RABBIT = 'rabbit'
    OTHER = 'other'


class PetSex(Enum):
    MALE = 'male'
    FEMALE = 'female'
    UNKNOWN = 'unknown'


@dataclass
class User:
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    is_active: bool
    date_joined: datetime
    last_login: Optional[datetime] = None
    is_superuser: bool = False
    is_staff: bool = False


@dataclass
class Superadmin:
    """Superadmin account - separate from veterinarians"""
    id: int
    user_id: int
    full_name: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    user: Optional[User] = None


@dataclass
class Veterinarian:
    id: int
    user_id: int
    full_name: str
    specialization: str
    license_number: str
    phone: str
    bio: str
    created_at: datetime
    branch: str = 'taguig'  # Branch location: taguig, pasig, makati
    user: Optional[User] = None


@dataclass
class Owner:
    id: int
    full_name: str
    email: str
    phone: str
    address: str
    created_at: datetime
    branch: str = 'taguig'  # Branch location: taguig, pasig, makati
    user_id: Optional[int] = None
    pets: List['Pet'] = None


@dataclass
class Pet:
    id: int
    owner_id: int
    name: str
    species: str
    breed: str
    sex: str
    birth_date: Optional[date]
    weight_kg: Optional[float]
    notes: str
    image: Optional[str] = None
    owner: Optional[Owner] = None
    appointments: List['Appointment'] = None
    medical_records: List['MedicalRecord'] = None
    prescriptions: List['Prescription'] = None
    vaccinations: List['Vaccination'] = None

    @property
    def image_url(self) -> Optional[str]:
        """Return the URL for the pet's image, if available."""
        if self.image:
            # Import here to avoid circular imports
            from utils.config import get_config

            # Try to get server URL from config
            config = get_config()

            # Check for production URL in a couple of places
            server_url = None
            if hasattr(config, 'get') and callable(config.get):
                server_url = config.get('app', {}).get('server_url') or \
                             config.get('api', {}).get('base_url')

            # Fall back to localhost if no server URL configured
            if not server_url:
                server_url = "http://localhost:8000"

            # Remove trailing slash if present
            server_url = server_url.rstrip('/')

            path = self.image.strip()
            # Normalize duplicate media prefix
            if path.startswith('/media/media/'):
                path = path.replace('/media/media/', '/media/', 1)
            # Normalize missing leading slash on 'media/'
            if path.startswith('media/'):
                path = '/' + path
            # If already absolute URL, return as-is
            if path.startswith(('http://', 'https://')):
                return path
            # If already looks like '/media/...'
            if path.startswith('/media/'):
                return f"{server_url}{path}"
            # Otherwise treat as a relative path under media root (e.g., 'pet_images/...')
            return f"{server_url}/media/{path}"
        return None


@dataclass
class Appointment:
    id: int
    pet_id: int
    date_time: datetime
    reason: str
    notes: str
    status: str
    pet: Optional[Pet] = None


@dataclass
class MedicalRecord:
    id: int
    pet_id: int
    visit_date: date
    condition: str
    treatment: str
    vet_notes: str
    pet: Optional[Pet] = None
    treatments: List['TreatmentRecord'] = None


@dataclass
class Prescription:
    id: int
    pet_id: int
    medication_name: str
    dosage: str
    instructions: str
    date_prescribed: date
    duration_days: Optional[int]
    is_active: bool
    pet: Optional[Pet] = None


@dataclass
class Vaccination:
    id: int
    pet_id: int
    vaccine_name: str
    date_given: date
    next_due: Optional[date]
    notes: str
    pet: Optional[Pet] = None


@dataclass
class Treatment:
    id: int
    name: str
    description: str
    duration_minutes: int
    price: float
    is_active: bool


@dataclass
class TreatmentRecord:
    id: int
    medical_record_id: int
    treatment_id: int
    notes: str
    performed_by_id: Optional[int]
    performed_at: datetime
    treatment: Optional[Treatment] = None
    performed_by: Optional[Veterinarian] = None


@dataclass
class VetNotification:
    id: int
    veterinarian_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime


@dataclass
class TreatmentType:
    id: int
    name: str
    description: str
    duration_minutes: int
    price: float
    is_active: bool


@dataclass
class Schedule:
    id: int
    veterinarian_id: int
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str   # Format: "HH:MM"
    end_time: str     # Format: "HH:MM"
    is_available: bool
    veterinarian: Optional[Veterinarian] = None