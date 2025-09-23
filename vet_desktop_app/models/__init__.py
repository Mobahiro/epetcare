"""
ePetCare Models Package
"""

# Import all models to make them available at the package level
try:
    from .models import *
except ImportError:
    print("Error importing models")