"""
Views package for the ePetCare Vet Desktop application.
"""

import os
import sys
import importlib.util
import logging

logger = logging.getLogger('epetcare')

# Special handling for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    logger.debug("Running from PyInstaller bundle - using special import handling for views")
    
    # Get the base directory
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the module paths
    main_window_path = os.path.join(base_dir, 'views', 'main_window.py')
    login_dialog_path = os.path.join(base_dir, 'views', 'login_dialog.py')
    register_dialog_path = os.path.join(base_dir, 'views', 'register_dialog.py')
    dashboard_view_path = os.path.join(base_dir, 'views', 'dashboard_view.py')
    appointments_view_path = os.path.join(base_dir, 'views', 'appointments_view.py')
    patients_view_path = os.path.join(base_dir, 'views', 'patients_view.py')
    settings_view_path = os.path.join(base_dir, 'views', 'settings_view.py')
    
    # Check if the files exist
    for path, name in [
        (main_window_path, 'main_window.py'),
        (login_dialog_path, 'login_dialog.py'),
        (register_dialog_path, 'register_dialog.py'),
        (dashboard_view_path, 'dashboard_view.py'),
        (appointments_view_path, 'appointments_view.py'),
        (patients_view_path, 'patients_view.py'),
        (settings_view_path, 'settings_view.py')
    ]:
        if not os.path.exists(path):
            logger.error(f"{name} not found at {path}")
    
    # Import the modules manually
    try:
        # Import main_window.py
        spec = importlib.util.spec_from_file_location("views.main_window", main_window_path)
        main_window = importlib.util.module_from_spec(spec)
        sys.modules['views.main_window'] = main_window
        spec.loader.exec_module(main_window)
        logger.debug("Successfully imported views.main_window")
        
        # Import login_dialog.py
        spec = importlib.util.spec_from_file_location("views.login_dialog", login_dialog_path)
        login_dialog = importlib.util.module_from_spec(spec)
        sys.modules['views.login_dialog'] = login_dialog
        spec.loader.exec_module(login_dialog)
        logger.debug("Successfully imported views.login_dialog")
        
        # Import register_dialog.py
        spec = importlib.util.spec_from_file_location("views.register_dialog", register_dialog_path)
        register_dialog = importlib.util.module_from_spec(spec)
        sys.modules['views.register_dialog'] = register_dialog
        spec.loader.exec_module(register_dialog)
        logger.debug("Successfully imported views.register_dialog")
        
        # Import dashboard_view.py
        spec = importlib.util.spec_from_file_location("views.dashboard_view", dashboard_view_path)
        dashboard_view = importlib.util.module_from_spec(spec)
        sys.modules['views.dashboard_view'] = dashboard_view
        spec.loader.exec_module(dashboard_view)
        logger.debug("Successfully imported views.dashboard_view")
        
        # Import appointments_view.py
        spec = importlib.util.spec_from_file_location("views.appointments_view", appointments_view_path)
        appointments_view = importlib.util.module_from_spec(spec)
        sys.modules['views.appointments_view'] = appointments_view
        spec.loader.exec_module(appointments_view)
        logger.debug("Successfully imported views.appointments_view")
        
        # Import patients_view.py
        spec = importlib.util.spec_from_file_location("views.patients_view", patients_view_path)
        patients_view = importlib.util.module_from_spec(spec)
        sys.modules['views.patients_view'] = patients_view
        spec.loader.exec_module(patients_view)
        logger.debug("Successfully imported views.patients_view")
        
        # Import settings_view.py
        spec = importlib.util.spec_from_file_location("views.settings_view", settings_view_path)
        settings_view = importlib.util.module_from_spec(spec)
        sys.modules['views.settings_view'] = settings_view
        spec.loader.exec_module(settings_view)
        logger.debug("Successfully imported views.settings_view")
        
        # Import commonly used classes
        MainWindow = main_window.MainWindow
        LoginDialog = login_dialog.LoginDialog
        RegisterDialog = register_dialog.RegisterDialog
        DashboardView = dashboard_view.DashboardView
        AppointmentsView = appointments_view.AppointmentsView
        PatientsView = patients_view.PatientsView
        SettingsView = settings_view.SettingsView
        
    except Exception as e:
        logger.error(f"Error importing view modules: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Set default values to avoid errors
        main_window = None
        login_dialog = None
        register_dialog = None
        dashboard_view = None
        appointments_view = None
        patients_view = None
        settings_view = None
        MainWindow = None
        LoginDialog = None
        RegisterDialog = None
        DashboardView = None
        AppointmentsView = None
        PatientsView = None
        SettingsView = None
else:
    # Running as a normal Python script
    logger.debug("Running as normal Python script - using standard imports for views")
    
    # Standard imports
    try:
        # Explicitly import all view modules to ensure they're included in the package
        from . import main_window
        from . import login_dialog
        from . import register_dialog
        from . import dashboard_view
        from . import appointments_view
        from . import patients_view
        from . import settings_view
        
        # Import commonly used classes for easier access
        from .main_window import MainWindow
        from .login_dialog import LoginDialog
        from .register_dialog import RegisterDialog
        from .dashboard_view import DashboardView
        from .appointments_view import AppointmentsView
        from .patients_view import PatientsView
        from .settings_view import SettingsView
    except ImportError as e:
        logger.error(f"Error importing view modules: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Define what's available from this package
__all__ = [
    'main_window', 'login_dialog', 'register_dialog', 'dashboard_view',
    'appointments_view', 'patients_view', 'settings_view',
    'MainWindow', 'LoginDialog', 'RegisterDialog', 'DashboardView',
    'AppointmentsView', 'PatientsView', 'SettingsView'
]