"""
Models package for the ePetCare Vet Desktop application.
"""

import os
import sys
import importlib.util
import logging

logger = logging.getLogger('epetcare')

# Special handling for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    logger.debug("Running from PyInstaller bundle - using special import handling for models")
    
    # Get the base directory
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the module paths
    models_path = os.path.join(base_dir, 'models', 'models.py')
    data_access_path = os.path.join(base_dir, 'models', 'data_access.py')
    
    # Check if the files exist
    if not os.path.exists(models_path):
        logger.error(f"models.py not found at {models_path}")
    if not os.path.exists(data_access_path):
        logger.error(f"data_access.py not found at {data_access_path}")
    
    # Import the modules manually
    try:
        # Import models.py
        spec = importlib.util.spec_from_file_location("models.models", models_path)
        models = importlib.util.module_from_spec(spec)
        sys.modules['models.models'] = models
        spec.loader.exec_module(models)
        logger.debug("Successfully imported models.models")
        
        # Import data_access.py
        spec = importlib.util.spec_from_file_location("models.data_access", data_access_path)
        data_access = importlib.util.module_from_spec(spec)
        sys.modules['models.data_access'] = data_access
        spec.loader.exec_module(data_access)
        logger.debug("Successfully imported models.data_access")
        
        # Import commonly used classes
        # These will be available from the models module directly
        User = models.User
        Veterinarian = models.Veterinarian
        Owner = models.Owner
        Pet = models.Pet
        Appointment = models.Appointment
        MedicalRecord = models.MedicalRecord
        Prescription = models.Prescription
        Vaccination = models.Vaccination
        Treatment = models.Treatment
        TreatmentRecord = models.TreatmentRecord
        VetNotification = models.VetNotification
        AppointmentStatus = models.AppointmentStatus
        PetSpecies = models.PetSpecies
        PetSex = models.PetSex
        
        # Import data access classes
        UserDataAccess = data_access.UserDataAccess
        VeterinarianDataAccess = data_access.VeterinarianDataAccess
        OwnerDataAccess = data_access.OwnerDataAccess
        PetDataAccess = data_access.PetDataAccess
        AppointmentDataAccess = data_access.AppointmentDataAccess
        MedicalRecordDataAccess = data_access.MedicalRecordDataAccess
        PrescriptionDataAccess = data_access.PrescriptionDataAccess
        
    except Exception as e:
        logger.error(f"Error importing modules: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Set default values to avoid errors
        models = None
        data_access = None
else:
    # Running as a normal Python script
    logger.debug("Running as normal Python script - using standard imports for models")
    
    # Standard imports
    try:
        from . import models
        from . import data_access
        
        # Import commonly used classes for easier access
        from .models import (
            User, Veterinarian, Owner, Pet, Appointment, MedicalRecord,
            Prescription, Vaccination, Treatment, TreatmentRecord, VetNotification,
            AppointmentStatus, PetSpecies, PetSex
        )
        
        from .data_access import (
            UserDataAccess, VeterinarianDataAccess, OwnerDataAccess, PetDataAccess,
            AppointmentDataAccess, MedicalRecordDataAccess, PrescriptionDataAccess
        )
    except ImportError as e:
        logger.error(f"Error importing modules: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Define what's available from this package
__all__ = [
    'models', 'data_access',
    'User', 'Veterinarian', 'Owner', 'Pet', 'Appointment', 'MedicalRecord',
    'Prescription', 'Vaccination', 'Treatment', 'TreatmentRecord', 'VetNotification',
    'AppointmentStatus', 'PetSpecies', 'PetSex',
    'UserDataAccess', 'VeterinarianDataAccess', 'OwnerDataAccess', 'PetDataAccess',
    'AppointmentDataAccess', 'MedicalRecordDataAccess', 'PrescriptionDataAccess'
]