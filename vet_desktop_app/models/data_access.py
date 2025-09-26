"""
Data access layer for the ePetCare Vet Desktop application.
This module provides classes to interact with the database.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import sys
import os
import importlib.util
import logging

logger = logging.getLogger('epetcare')

# Special handling for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    logger.debug("data_access.py: Using special import handling for frozen app")
    
    # Import DatabaseManager from utils.database
    try:
        try:
            # Prefer Postgres manager if pg_db is configured
            from utils.pg_db import PostgresDatabaseManager as DatabaseManager
        except ImportError:
            from utils.database import DatabaseManager
        logger.debug("Successfully imported DatabaseManager from utils.database")
    except ImportError:
        logger.error("Failed to import DatabaseManager from utils.database")
        # Try to import directly
        try:
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            database_path = os.path.join(base_dir, 'utils', 'database.py')
            if os.path.exists(database_path):
                spec = importlib.util.spec_from_file_location("utils.database", database_path)
                database_module = importlib.util.module_from_spec(spec)
                sys.modules['utils.database'] = database_module
                spec.loader.exec_module(database_module)
                DatabaseManager = database_module.DatabaseManager
                logger.debug(f"Imported DatabaseManager from {database_path}")
            else:
                logger.error(f"database.py not found at {database_path}")
                # Define a dummy DatabaseManager as fallback
                class DatabaseManager:
                    def __init__(self): pass
        except Exception as e:
            logger.error(f"Error importing DatabaseManager: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Define a dummy DatabaseManager as fallback
            class DatabaseManager:
                def __init__(self): pass
    
    # Import model classes
    try:
        # Try importing from models.models first
        try:
            from models.models import (
                User, Veterinarian, Owner, Pet, Appointment, MedicalRecord,
                Prescription, Vaccination, Treatment, TreatmentRecord, VetNotification,
                TreatmentType, Schedule
            )
            logger.debug("Successfully imported model classes from models.models")
        except ImportError:
            logger.error("Failed to import model classes from models.models")
            # Try to import directly
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
            models_path = os.path.join(base_dir, 'models', 'models.py')
            if os.path.exists(models_path):
                spec = importlib.util.spec_from_file_location("models.models", models_path)
                models_module = importlib.util.module_from_spec(spec)
                sys.modules['models.models'] = models_module
                spec.loader.exec_module(models_module)
                
                # Get the classes from the module
                User = models_module.User
                Veterinarian = models_module.Veterinarian
                Owner = models_module.Owner
                Pet = models_module.Pet
                Appointment = models_module.Appointment
                MedicalRecord = models_module.MedicalRecord
                Prescription = models_module.Prescription
                Vaccination = models_module.Vaccination
                Treatment = models_module.Treatment
                TreatmentRecord = models_module.TreatmentRecord
                VetNotification = models_module.VetNotification
                TreatmentType = models_module.TreatmentType
                Schedule = models_module.Schedule
                
                logger.debug(f"Imported model classes from {models_path}")
            else:
                logger.error(f"models.py not found at {models_path}")
                raise ImportError(f"models.py not found at {models_path}")
    except Exception as e:
        logger.error(f"Error importing model classes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
else:
    # Running as a normal Python script - use regular imports
    try:
        from utils.pg_db import PostgresDatabaseManager as DatabaseManager
    except ImportError:
        from utils.database import DatabaseManager
    try:
        # Try relative import first
        from .models import (
            User, Veterinarian, Owner, Pet, Appointment, MedicalRecord,
            Prescription, Vaccination, Treatment, TreatmentRecord, VetNotification,
            TreatmentType, Schedule
        )
    except ImportError:
        # Fall back to absolute import
        from models.models import (
            User, Veterinarian, Owner, Pet, Appointment, MedicalRecord,
            Prescription, Vaccination, Treatment, TreatmentRecord, VetNotification,
            TreatmentType, Schedule
        )


class DataAccessBase:
    """Base class for data access"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def _row_to_dict(self, row):
        """Convert a sqlite3.Row to a dictionary"""
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}

    # Parsing helpers to handle both strings (SQLite style) and native Python types (psycopg2)
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        # If it's a date, upcast to datetime at midnight
        if isinstance(value, date) and not isinstance(value, datetime):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            v = value.strip()
            # Normalize trailing Z to +00:00
            if v.endswith('Z'):
                v = v[:-1] + '+00:00'
            try:
                return datetime.fromisoformat(v)
            except Exception:
                # Try without fractional seconds if present
                if '.' in v:
                    try:
                        base = v.split('.')[0]
                        return datetime.fromisoformat(base)
                    except Exception:
                        pass
        return None

    def _parse_date(self, value: Any) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            v = value.strip()
            # Accept full ISO strings by splitting date portion
            if 'T' in v:
                v = v.split('T')[0]
            try:
                return date.fromisoformat(v)
            except Exception:
                pass
        return None


class UserDataAccess(DataAccessBase):
    """Data access for User model"""
    
    def get_by_id(self, user_id: int) -> 'Optional[User]':
        """Get a user by ID"""
        success, result = self.db.fetch_by_id('auth_user', user_id)
        if not success:
            return None
        
        user_dict = self._row_to_dict(result)
        return User(
            id=user_dict['id'],
            username=user_dict['username'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'],
            email=user_dict['email'],
            is_active=bool(user_dict['is_active']),
            date_joined=self._parse_datetime(user_dict['date_joined']),
            last_login=self._parse_datetime(user_dict['last_login'])
        )
    
    def get_by_username(self, username: str) -> 'Optional[User]':
        """Get a user by username"""
        query = "SELECT * FROM auth_user WHERE username = ?"
        success, result = self.db.execute_query(query, (username,))
        
        if not success or not result:
            return None
        
        user_dict = self._row_to_dict(result[0])
        return User(
            id=user_dict['id'],
            username=user_dict['username'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'],
            email=user_dict['email'],
            is_active=bool(user_dict['is_active']),
            date_joined=self._parse_datetime(user_dict['date_joined']),
            last_login=self._parse_datetime(user_dict['last_login'])
        )
    
    def get_by_email(self, email: str) -> 'Optional[User]':
        """Get a user by email"""
        query = "SELECT * FROM auth_user WHERE email = ?"
        success, result = self.db.execute_query(query, (email,))
        
        if not success or not result:
            return None
        
        user_dict = self._row_to_dict(result[0])
        return User(
            id=user_dict['id'],
            username=user_dict['username'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'],
            email=user_dict['email'],
            is_active=bool(user_dict['is_active']),
            date_joined=self._parse_datetime(user_dict['date_joined']),
            last_login=self._parse_datetime(user_dict['last_login'])
        )
    
    def authenticate(self, username: str, password: str) -> 'Optional[User]':
        """Authenticate a user"""
        import hashlib
        import base64
        import re
        
        query = "SELECT * FROM auth_user WHERE username = ?"
        success, result = self.db.execute_query(query, (username,))
        
        if not success or not result:
            return None
        
        user_dict = self._row_to_dict(result[0])
        
        # Get the password from the database
        # In Django, passwords are stored as: algorithm$iterations$salt$hash
        stored_password = user_dict.get('password', '')
        
        # Check if this is a Django-style password
        if '$' in stored_password:
            try:
                # Parse the components
                parts = stored_password.split('$')
                if len(parts) >= 4:
                    algorithm = parts[0]
                    iterations = int(parts[1])
                    salt = parts[2]
                    stored_hash = parts[3]
                    
                    # Handle PBKDF2 algorithm (most common in Django)
                    if algorithm == 'pbkdf2_sha256':
                        import hashlib
                        import binascii
                        
                        # Convert iterations to integer
                        iterations = int(iterations)
                        
                        # Generate hash from the provided password
                        dk = hashlib.pbkdf2_hmac(
                            'sha256', 
                            password.encode('utf-8'), 
                            salt.encode('utf-8'), 
                            iterations
                        )
                        computed_hash = binascii.hexlify(dk).decode('ascii')
                        
                        # Compare the hashes
                        if computed_hash == stored_hash:
                            # Password matches
                            return User(
                                id=user_dict['id'],
                                username=user_dict['username'],
                                first_name=user_dict['first_name'],
                                last_name=user_dict['last_name'],
                                email=user_dict['email'],
                                is_active=bool(user_dict['is_active']),
                                date_joined=self._parse_datetime(user_dict['date_joined']),
                                last_login=self._parse_datetime(user_dict['last_login'])
                            )
                    # Handle other algorithms as needed
            except Exception as e:
                print(f"Error verifying password: {e}")
                pass
        else:
            # For development/testing only: check if passwords match directly
            # This should never be used in production
            if stored_password == password:
                return User(
                    id=user_dict['id'],
                    username=user_dict['username'],
                    first_name=user_dict['first_name'],
                    last_name=user_dict['last_name'],
                    email=user_dict['email'],
                    is_active=bool(user_dict['is_active']),
                    date_joined=self._parse_datetime(user_dict['date_joined']),
                    last_login=self._parse_datetime(user_dict['last_login'])
                )
        
        return None
    
    def create_user(self, username: str, password: str, email: str, first_name: str, last_name: str) -> Tuple[bool, Union[int, str]]:
        """Create a new user"""
        # Check if username already exists
        if self.get_by_username(username):
            return False, "Username already exists"
        
        # Check if email already exists
        if self.get_by_email(email):
            return False, "Email already exists"
        
        # Hash the password using PBKDF2 (similar to Django's default)
        import hashlib
        import binascii
        import os
        
        # Generate a random salt
        salt = os.urandom(16).hex()
        iterations = 390000  # Django's default iterations as of 2023
        
        # Hash the password
        dk = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            iterations
        )
        hashed_password = binascii.hexlify(dk).decode('ascii')
        
        # Format the password in Django's format: algorithm$iterations$salt$hash
        password_string = f"pbkdf2_sha256${iterations}${salt}${hashed_password}"
        
        # Create user data
        now = datetime.now().isoformat()
        user_data = {
            'username': username,
            'password': password_string,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
            'date_joined': now,
            'last_login': None
        }
        
        # Insert user
        return self.db.insert('auth_user', user_data)
    
    def update_last_login(self, user_id: int) -> bool:
        """Update the last login time for a user"""
        now = datetime.now().isoformat()
        data = {'last_login': now}
        success, _ = self.db.update('auth_user', data, user_id)
        return success


class VeterinarianDataAccess(DataAccessBase):
    """Data access for Veterinarian model"""
    
    def get_by_id(self, vet_id: int) -> Optional[Veterinarian]:
        """Get a veterinarian by ID"""
        success, result = self.db.fetch_by_id('vet_veterinarian', vet_id)
        if not success:
            return None
        
        vet_dict = self._row_to_dict(result)
        return Veterinarian(
            id=vet_dict['id'],
            user_id=vet_dict['user_id'],
            full_name=vet_dict['full_name'],
            specialization=vet_dict['specialization'],
            license_number=vet_dict['license_number'],
            phone=vet_dict['phone'],
            bio=vet_dict['bio'],
            created_at=self._parse_datetime(vet_dict['created_at'])
        )
    
    def get_by_user_id(self, user_id: int) -> Optional[Veterinarian]:
        """Get a veterinarian by user ID"""
        query = "SELECT * FROM vet_veterinarian WHERE user_id = ?"
        success, result = self.db.execute_query(query, (user_id,))
        
        if not success or not result:
            return None
        
        vet_dict = self._row_to_dict(result[0])
        return Veterinarian(
            id=vet_dict['id'],
            user_id=vet_dict['user_id'],
            full_name=vet_dict['full_name'],
            specialization=vet_dict['specialization'],
            license_number=vet_dict['license_number'],
            phone=vet_dict['phone'],
            bio=vet_dict['bio'],
            created_at=self._parse_datetime(vet_dict['created_at'])
        )
    
    def get_by_license_number(self, license_number: str) -> Optional[Veterinarian]:
        """Get a veterinarian by license number"""
        query = "SELECT * FROM vet_veterinarian WHERE license_number = ?"
        success, result = self.db.execute_query(query, (license_number,))
        
        if not success or not result:
            return None
        
        vet_dict = self._row_to_dict(result[0])
        return Veterinarian(
            id=vet_dict['id'],
            user_id=vet_dict['user_id'],
            full_name=vet_dict['full_name'],
            specialization=vet_dict['specialization'],
            license_number=vet_dict['license_number'],
            phone=vet_dict['phone'],
            bio=vet_dict['bio'],
            created_at=self._parse_datetime(vet_dict['created_at'])
        )
    
    def get_all(self) -> List[Veterinarian]:
        """Get all veterinarians"""
        success, result = self.db.fetch_all('vet_veterinarian')
        if not success:
            return []
        
        vets = []
        for row in result:
            vet_dict = self._row_to_dict(row)
            vets.append(Veterinarian(
                id=vet_dict['id'],
                user_id=vet_dict['user_id'],
                full_name=vet_dict['full_name'],
                specialization=vet_dict['specialization'],
                license_number=vet_dict['license_number'],
                phone=vet_dict['phone'],
                bio=vet_dict['bio'],
                created_at=self._parse_datetime(vet_dict['created_at'])
            ))
        
        return vets
    
    def create(self, user_id: int, full_name: str, specialization: str, 
               license_number: str, phone: str, bio: str) -> Tuple[bool, Union[int, str]]:
        """Create a new veterinarian"""
        # Check if license number already exists
        if license_number and self.get_by_license_number(license_number):
            return False, "License number already exists"
        
        # Check if user already has a vet profile
        if self.get_by_user_id(user_id):
            return False, "User already has a veterinarian profile"
        
        # Create veterinarian data
        now = datetime.now().isoformat()
        vet_data = {
            'user_id': user_id,
            'full_name': full_name,
            'specialization': specialization,
            'license_number': license_number,
            'phone': phone,
            'bio': bio,
            'created_at': now
        }
        
        # Insert veterinarian
        return self.db.insert('vet_veterinarian', vet_data)
    
    def update(self, vet_id: int, full_name: str = None, specialization: str = None,
               license_number: str = None, phone: str = None, bio: str = None) -> Tuple[bool, Union[int, str]]:
        """Update an existing veterinarian"""
        # Get current vet data
        vet = self.get_by_id(vet_id)
        if not vet:
            return False, "Veterinarian not found"
        
        # Check if license number already exists and is different from current
        if license_number and license_number != vet.license_number:
            existing_vet = self.get_by_license_number(license_number)
            if existing_vet and existing_vet.id != vet_id:
                return False, "License number already exists"
        
        # Update only provided fields
        vet_data = {}
        if full_name is not None:
            vet_data['full_name'] = full_name
        if specialization is not None:
            vet_data['specialization'] = specialization
        if license_number is not None:
            vet_data['license_number'] = license_number
        if phone is not None:
            vet_data['phone'] = phone
        if bio is not None:
            vet_data['bio'] = bio
        
        # If no fields to update, return success
        if not vet_data:
            return True, vet_id
        
        # Update veterinarian
        return self.db.update('vet_veterinarian', vet_data, vet_id)


class OwnerDataAccess(DataAccessBase):
    """Data access for Owner model"""
    
    def get_by_id(self, owner_id: int) -> Optional[Owner]:
        """Get an owner by ID"""
        success, result = self.db.fetch_by_id('clinic_owner', owner_id)
        if not success:
            return None
        
        owner_dict = self._row_to_dict(result)
        return Owner(
            id=owner_dict['id'],
            full_name=owner_dict['full_name'],
            email=owner_dict['email'],
            phone=owner_dict['phone'],
            address=owner_dict['address'],
            created_at=self._parse_datetime(owner_dict['created_at']),
            user_id=owner_dict['user_id']
        )
    
    def search(self, query: str, limit: int = 50) -> List[Owner]:
        """Search owners by name, email, or phone"""
        search_query = f"%{query}%"
        sql = """
            SELECT * FROM clinic_owner 
            WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ?
            LIMIT ?
        """
        success, result = self.db.execute_query(sql, (search_query, search_query, search_query, limit))
        
        if not success:
            return []
        
        owners = []
        for row in result:
            owner_dict = self._row_to_dict(row)
            owners.append(Owner(
                id=owner_dict['id'],
                full_name=owner_dict['full_name'],
                email=owner_dict['email'],
                phone=owner_dict['phone'],
                address=owner_dict['address'],
                created_at=self._parse_datetime(owner_dict['created_at']),
                user_id=owner_dict['user_id']
            ))
        
        return owners
    
    def get_all(self, limit: int = 100) -> List[Owner]:
        """Get all owners with optional limit"""
        success, result = self.db.fetch_all('clinic_owner', order_by='full_name', limit=limit)
        if not success:
            return []
        
        owners = []
        for row in result:
            owner_dict = self._row_to_dict(row)
            owners.append(Owner(
                id=owner_dict['id'],
                full_name=owner_dict['full_name'],
                email=owner_dict['email'],
                phone=owner_dict['phone'],
                address=owner_dict['address'],
                created_at=self._parse_datetime(owner_dict['created_at']),
                user_id=owner_dict['user_id']
            ))
        
        return owners


class PetDataAccess(DataAccessBase):
    """Data access for Pet model"""
    
    def get_by_id(self, pet_id: int) -> Optional[Pet]:
        """Get a pet by ID"""
        success, result = self.db.fetch_by_id('clinic_pet', pet_id)
        if not success:
            return None
        
        pet_dict = self._row_to_dict(result)
        return Pet(
            id=pet_dict['id'],
            owner_id=pet_dict['owner_id'],
            name=pet_dict['name'],
            species=pet_dict['species'],
            breed=pet_dict['breed'],
            sex=pet_dict['sex'],
            birth_date=self._parse_date(pet_dict['birth_date']) if pet_dict['birth_date'] else None,
            weight_kg=float(pet_dict['weight_kg']) if pet_dict['weight_kg'] else None,
            notes=pet_dict['notes']
        )
    
    def get_by_owner(self, owner_id: int) -> List[Pet]:
        """Get pets by owner ID"""
        success, result = self.db.fetch_all('clinic_pet', conditions={'owner_id': owner_id})
        if not success:
            return []
        
        pets = []
        for row in result:
            pet_dict = self._row_to_dict(row)
            pets.append(Pet(
                id=pet_dict['id'],
                owner_id=pet_dict['owner_id'],
                name=pet_dict['name'],
                species=pet_dict['species'],
                breed=pet_dict['breed'],
                sex=pet_dict['sex'],
                birth_date=self._parse_date(pet_dict['birth_date']) if pet_dict['birth_date'] else None,
                weight_kg=float(pet_dict['weight_kg']) if pet_dict['weight_kg'] else None,
                notes=pet_dict['notes']
            ))
        
        return pets
    
    def delete(self, pet_id: int) -> Tuple[bool, Union[int, str]]:
        """Delete a pet"""
        return self.db.delete('clinic_pet', pet_id)
    
    def search(self, query: str, limit: int = 50) -> List[Pet]:
        """Search pets by name or breed"""
        search_query = f"%{query}%"
        sql = """
            SELECT p.* FROM clinic_pet p
            LEFT JOIN clinic_owner o ON p.owner_id = o.id
            WHERE p.name LIKE ? OR p.breed LIKE ? OR o.full_name LIKE ?
            LIMIT ?
        """
        success, result = self.db.execute_query(sql, (search_query, search_query, search_query, limit))
        
        if not success:
            return []
        
        pets = []
        for row in result:
            pet_dict = self._row_to_dict(row)
            pets.append(Pet(
                id=pet_dict['id'],
                owner_id=pet_dict['owner_id'],
                name=pet_dict['name'],
                species=pet_dict['species'],
                breed=pet_dict['breed'],
                sex=pet_dict['sex'],
                birth_date=self._parse_date(pet_dict['birth_date']) if pet_dict['birth_date'] else None,
                weight_kg=float(pet_dict['weight_kg']) if pet_dict['weight_kg'] else None,
                notes=pet_dict['notes']
            ))
        
        return pets


class AppointmentDataAccess(DataAccessBase):
    """Data access for Appointment model"""
    
    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Get an appointment by ID"""
        success, result = self.db.fetch_by_id('clinic_appointment', appointment_id)
        if not success:
            return None
        
        appt_dict = self._row_to_dict(result)
        return Appointment(
            id=appt_dict['id'],
            pet_id=appt_dict['pet_id'],
            date_time=self._parse_datetime(appt_dict['date_time']),
            reason=appt_dict['reason'],
            notes=appt_dict['notes'],
            status=appt_dict['status']
        )
    
    def get_by_pet(self, pet_id: int) -> List[Appointment]:
        """Get appointments by pet ID"""
        success, result = self.db.fetch_all('clinic_appointment', conditions={'pet_id': pet_id})
        if not success:
            return []
        
        appointments = []
        for row in result:
            appt_dict = self._row_to_dict(row)
            appointments.append(Appointment(
                id=appt_dict['id'],
                pet_id=appt_dict['pet_id'],
                date_time=self._parse_datetime(appt_dict['date_time']),
                reason=appt_dict['reason'],
                notes=appt_dict['notes'],
                status=appt_dict['status']
            ))
        
        return appointments
    
    def get_all_appointments(self) -> List[Appointment]:
        """Get all appointments"""
        sql = """
            SELECT a.*, p.name as pet_name, o.full_name as owner_name 
            FROM clinic_appointment a
            JOIN clinic_pet p ON a.pet_id = p.id
            JOIN clinic_owner o ON p.owner_id = o.id
            ORDER BY a.date_time DESC
        """
        success, result = self.db.execute_query(sql)
        
        if not success:
            return []
        
        appointments = []
        for row in result:
            appt_dict = self._row_to_dict(row)
            appointment = Appointment(
                id=appt_dict['id'],
                pet_id=appt_dict['pet_id'],
                date_time=self._parse_datetime(appt_dict['date_time']),
                reason=appt_dict['reason'],
                notes=appt_dict['notes'],
                status=appt_dict['status']
            )
            # Add pet with minimal info
            appointment.pet = Pet(
                id=appt_dict['pet_id'],
                owner_id=0,  # We don't have this in the result
                name=appt_dict['pet_name'],
                species='',
                breed='',
                sex='',
                birth_date=None,
                weight_kg=None,
                notes=''
            )
            appointments.append(appointment)
        
        return appointments
    def get_upcoming(self, days: int = 7) -> List[Appointment]:
        """Get upcoming appointments for the next X days"""
        now = datetime.now()
        now_str = now.isoformat()
        # Use timedelta for proper date calculation instead of replacing day
        future = now + timedelta(days=days)
        future = future.replace(hour=23, minute=59, second=59)
        future_str = future.isoformat()
        
        sql = """
            SELECT a.*, p.name as pet_name, o.full_name as owner_name 
            FROM clinic_appointment a
            JOIN clinic_pet p ON a.pet_id = p.id
            JOIN clinic_owner o ON p.owner_id = o.id
            WHERE a.date_time >= ? AND a.date_time <= ? AND a.status = 'scheduled'
            ORDER BY a.date_time
        """
        success, result = self.db.execute_query(sql, (now_str, future_str))
        
        if not success:
            return []
        
        appointments = []
        for row in result:
            appt_dict = self._row_to_dict(row)
            appointment = Appointment(
                id=appt_dict['id'],
                pet_id=appt_dict['pet_id'],
                date_time=self._parse_datetime(appt_dict['date_time']),
                reason=appt_dict['reason'],
                notes=appt_dict['notes'],
                status=appt_dict['status']
            )
            # Add pet with minimal info
            appointment.pet = Pet(
                id=appt_dict['pet_id'],
                owner_id=0,  # We don't have this in the result
                name=appt_dict['pet_name'],
                species='',
                breed='',
                sex='',
                birth_date=None,
                weight_kg=None,
                notes=''
            )
            appointments.append(appointment)
        
        return appointments
    
    def create(self, appointment: Appointment) -> Tuple[bool, Union[int, str]]:
        """Create a new appointment"""
        data = {
            'pet_id': appointment.pet_id,
            'date_time': appointment.date_time.isoformat(),
            'reason': appointment.reason,
            'notes': appointment.notes,
            'status': appointment.status
        }
        
        return self.db.insert('clinic_appointment', data)
    
    def update(self, appointment: Appointment) -> Tuple[bool, Union[int, str]]:
        """Update an existing appointment"""
        data = {
            'pet_id': appointment.pet_id,
            'date_time': appointment.date_time.isoformat(),
            'reason': appointment.reason,
            'notes': appointment.notes,
            'status': appointment.status
        }
        
        return self.db.update('clinic_appointment', data, appointment.id)
    
    def delete(self, appointment_id: int) -> Tuple[bool, Union[int, str]]:
        """Delete an appointment"""
        return self.db.delete('clinic_appointment', appointment_id)


class MedicalRecordDataAccess(DataAccessBase):
    """Data access for MedicalRecord model"""
    
    def get_by_id(self, record_id: int) -> Optional[MedicalRecord]:
        """Get a medical record by ID"""
        success, result = self.db.fetch_by_id('clinic_medicalrecord', record_id)
        if not success:
            return None
        
        record_dict = self._row_to_dict(result)
        return MedicalRecord(
            id=record_dict['id'],
            pet_id=record_dict['pet_id'],
            visit_date=self._parse_date(record_dict['visit_date']),
            condition=record_dict['condition'],
            treatment=record_dict['treatment'],
            vet_notes=record_dict['vet_notes']
        )
    
    def get_by_pet(self, pet_id: int) -> List[MedicalRecord]:
        """Get medical records by pet ID"""
        success, result = self.db.fetch_all(
            'clinic_medicalrecord', 
            conditions={'pet_id': pet_id},
            order_by='visit_date DESC'
        )
        if not success:
            return []
        
        records = []
        for row in result:
            record_dict = self._row_to_dict(row)
            records.append(MedicalRecord(
                id=record_dict['id'],
                pet_id=record_dict['pet_id'],
                visit_date=self._parse_date(record_dict['visit_date']),
                condition=record_dict['condition'],
                treatment=record_dict['treatment'],
                vet_notes=record_dict['vet_notes']
            ))
        
        return records
    
    def create(self, record: MedicalRecord) -> Tuple[bool, Union[int, str]]:
        """Create a new medical record"""
        data = {
            'pet_id': record.pet_id,
            'visit_date': record.visit_date.isoformat(),
            'condition': record.condition,
            'treatment': record.treatment,
            'vet_notes': record.vet_notes
        }
        
        return self.db.insert('clinic_medicalrecord', data)
    
    def update(self, record: MedicalRecord) -> Tuple[bool, Union[int, str]]:
        """Update an existing medical record"""
        data = {
            'pet_id': record.pet_id,
            'visit_date': record.visit_date.isoformat(),
            'condition': record.condition,
            'treatment': record.treatment,
            'vet_notes': record.vet_notes
        }
        
        return self.db.update('clinic_medicalrecord', data, record.id)
    
    def delete(self, record_id: int) -> Tuple[bool, Union[int, str]]:
        """Delete a medical record"""
        return self.db.delete('clinic_medicalrecord', record_id)


class PrescriptionDataAccess(DataAccessBase):
    """Data access for Prescription model"""
    
    def get_by_id(self, prescription_id: int) -> Optional[Prescription]:
        """Get a prescription by ID"""
        success, result = self.db.fetch_by_id('clinic_prescription', prescription_id)
        if not success:
            return None
        
        prescription_dict = self._row_to_dict(result)
        return Prescription(
            id=prescription_dict['id'],
            pet_id=prescription_dict['pet_id'],
            medication_name=prescription_dict['medication_name'],
            dosage=prescription_dict['dosage'],
            instructions=prescription_dict['instructions'],
            date_prescribed=self._parse_date(prescription_dict['date_prescribed']),
            duration_days=prescription_dict['duration_days'],
            is_active=bool(prescription_dict['is_active'])
        )
    
    def get_by_pet(self, pet_id: int, active_only: bool = False) -> List[Prescription]:
        """Get prescriptions by pet ID"""
        conditions = {'pet_id': pet_id}
        if active_only:
            conditions['is_active'] = True
            
        success, result = self.db.fetch_all(
            'clinic_prescription', 
            conditions=conditions,
            order_by='date_prescribed DESC'
        )
        if not success:
            return []
        
        prescriptions = []
        for row in result:
            prescription_dict = self._row_to_dict(row)
            prescriptions.append(Prescription(
                id=prescription_dict['id'],
                pet_id=prescription_dict['pet_id'],
                medication_name=prescription_dict['medication_name'],
                dosage=prescription_dict['dosage'],
                instructions=prescription_dict['instructions'],
                date_prescribed=self._parse_date(prescription_dict['date_prescribed']),
                duration_days=prescription_dict['duration_days'],
                is_active=bool(prescription_dict['is_active'])
            ))
        
        return prescriptions
    
    def create(self, prescription: Prescription) -> Tuple[bool, Union[int, str]]:
        """Create a new prescription"""
        data = {
            'pet_id': prescription.pet_id,
            'medication_name': prescription.medication_name,
            'dosage': prescription.dosage,
            'instructions': prescription.instructions,
            'date_prescribed': prescription.date_prescribed.isoformat(),
            'duration_days': prescription.duration_days,
            'is_active': bool(prescription.is_active)
        }
        
        return self.db.insert('clinic_prescription', data)
    
    def update(self, prescription: Prescription) -> Tuple[bool, Union[int, str]]:
        """Update an existing prescription"""
        data = {
            'pet_id': prescription.pet_id,
            'medication_name': prescription.medication_name,
            'dosage': prescription.dosage,
            'instructions': prescription.instructions,
            'date_prescribed': prescription.date_prescribed.isoformat(),
            'duration_days': prescription.duration_days,
            'is_active': bool(prescription.is_active)
        }
        
        return self.db.update('clinic_prescription', data, prescription.id)
    
    def delete(self, prescription_id: int) -> Tuple[bool, Union[int, str]]:
        """Delete a prescription"""
        return self.db.delete('clinic_prescription', prescription_id)


class TreatmentTypeDataAccess(DataAccessBase):
    """Data access for TreatmentType model"""
    
    def get_by_id(self, treatment_type_id: int) -> Optional[TreatmentType]:
        """Get a treatment type by ID"""
        query = """
            SELECT * FROM vet_treatmenttype WHERE id = ?
        """
        success, result = self.db.execute_query(query, (treatment_type_id,))
        
        if not success or not result:
            return None
        
        treatment_dict = self._row_to_dict(result[0])
        return TreatmentType(
            id=treatment_dict['id'],
            name=treatment_dict['name'],
            description=treatment_dict['description'],
            duration_minutes=treatment_dict['duration_minutes'],
            price=float(treatment_dict['price']),
            is_active=bool(treatment_dict['is_active'])
        )
    
    def get_all_active(self) -> List[TreatmentType]:
        """Get all active treatment types"""
        query = """
            SELECT * FROM vet_treatmenttype WHERE is_active = TRUE ORDER BY name
        """
        success, result = self.db.execute_query(query)
        
        if not success:
            return []
        
        treatments = []
        for row in result:
            treatment_dict = self._row_to_dict(row)
            treatments.append(TreatmentType(
                id=treatment_dict['id'],
                name=treatment_dict['name'],
                description=treatment_dict['description'],
                duration_minutes=treatment_dict['duration_minutes'],
                price=float(treatment_dict['price']),
                is_active=bool(treatment_dict['is_active'])
            ))
        
        return treatments
    
    def create(self, treatment_type: TreatmentType) -> Tuple[bool, Union[int, str]]:
        """Create a new treatment type"""
        data = {
            'name': treatment_type.name,
            'description': treatment_type.description,
            'duration_minutes': treatment_type.duration_minutes,
            'price': treatment_type.price,
            'is_active': bool(treatment_type.is_active)
        }
        
        return self.db.insert('vet_treatmenttype', data)
    
    def update(self, treatment_type: TreatmentType) -> Tuple[bool, Union[int, str]]:
        """Update an existing treatment type"""
        data = {
            'name': treatment_type.name,
            'description': treatment_type.description,
            'duration_minutes': treatment_type.duration_minutes,
            'price': treatment_type.price,
            'is_active': bool(treatment_type.is_active)
        }
        
        return self.db.update('vet_treatmenttype', data, treatment_type.id)


class ScheduleDataAccess(DataAccessBase):
    """Data access for Schedule model"""
    
    def get_by_vet(self, vet_id: int) -> List[Schedule]:
        """Get schedule by veterinarian ID"""
        query = """
            SELECT * FROM vet_schedule WHERE veterinarian_id = ? ORDER BY day_of_week, start_time
        """
        success, result = self.db.execute_query(query, (vet_id,))
        
        if not success:
            return []
        
        schedules = []
        for row in result:
            schedule_dict = self._row_to_dict(row)
            schedules.append(Schedule(
                id=schedule_dict['id'],
                veterinarian_id=schedule_dict['veterinarian_id'],
                day_of_week=schedule_dict['day_of_week'],
                start_time=schedule_dict['start_time'],
                end_time=schedule_dict['end_time'],
                is_available=bool(schedule_dict['is_available'])
            ))
        
        return schedules
    
    def create(self, schedule: Schedule) -> Tuple[bool, Union[int, str]]:
        """Create a new schedule entry"""
        data = {
            'veterinarian_id': schedule.veterinarian_id,
            'day_of_week': schedule.day_of_week,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'is_available': bool(schedule.is_available)
        }
        
        return self.db.insert('vet_schedule', data)
    
    def update(self, schedule: Schedule) -> Tuple[bool, Union[int, str]]:
        """Update an existing schedule entry"""
        data = {
            'veterinarian_id': schedule.veterinarian_id,
            'day_of_week': schedule.day_of_week,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'is_available': bool(schedule.is_available)
        }
        
        return self.db.update('vet_schedule', data, schedule.id)
    
    def delete(self, schedule_id: int) -> Tuple[bool, Union[int, str]]:
        """Delete a schedule entry"""
        return self.db.delete('vet_schedule', schedule_id)
