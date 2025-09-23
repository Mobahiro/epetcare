"""
Utilities package for the ePetCare Vet Desktop application.
"""

# Explicitly import all utility modules to ensure they're included in the package
from . import config
from . import database
from . import notification_manager

# Import commonly used classes and functions for easier access
from .config import load_config, save_config, get_config_value, set_config_value
from .database import setup_database_connection, get_connection, close_connection, DatabaseManager
from .notification_manager import NotificationManager

__all__ = [
    'config', 'database', 'notification_manager',
    'load_config', 'save_config', 'get_config_value', 'set_config_value',
    'setup_database_connection', 'get_connection', 'close_connection', 'DatabaseManager',
    'NotificationManager'
]