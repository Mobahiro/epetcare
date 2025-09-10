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
    user: Optional[User] = None


@dataclass
class Owner:
    id: int
    full_name: str
    email: str
    phone: str
    address: str
    created_at: datetime
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
    owner: Optional[Owner] = None
    appointments: List['Appointment'] = None
    medical_records: List['MedicalRecord'] = None
    prescriptions: List['Prescription'] = None
    vaccinations: List['Vaccination'] = None


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
