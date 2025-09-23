"""
Package initialization script for PyInstaller.
This script is used as a runtime hook to initialize packages properly in the PyInstaller bundle.
"""

import os
import sys
import importlib
import logging

logger = logging.getLogger('epetcare')

def init_packages():
    """Initialize packages for PyInstaller."""
    logger.debug("Initializing packages for PyInstaller...")
    
    # Only run this for frozen applications
    if not getattr(sys, 'frozen', False):
        logger.debug("Not a frozen application, skipping package initialization")
        return
    
    # Get the base directory
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    logger.debug(f"Base directory: {base_dir}")
    
    # Add the base directory to the path if not already there
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
        logger.debug(f"Added {base_dir} to Python path")
    
    # Add module directories to the path
    for module_dir in ['views', 'utils', 'models', 'controllers']:
        module_path = os.path.join(base_dir, module_dir)
        if os.path.exists(module_path) and module_path not in sys.path:
            sys.path.insert(0, module_path)
            logger.debug(f"Added {module_path} to Python path")
    
    # Initialize the models package
    try:
        # Create the models package if it doesn't exist
        if 'models' not in sys.modules:
            logger.debug("Creating models package")
            models_module = importlib.util.module_from_name("models")
            sys.modules['models'] = models_module
        
        # Import models.py
        models_path = os.path.join(base_dir, 'models', 'models.py')
        if os.path.exists(models_path):
            logger.debug(f"Importing models.py from {models_path}")
            spec = importlib.util.spec_from_file_location("models.models", models_path)
            models_module = importlib.util.module_from_spec(spec)
            sys.modules['models.models'] = models_module
            spec.loader.exec_module(models_module)
            logger.debug("Successfully imported models.models")
        else:
            logger.error(f"models.py not found at {models_path}")
        
        # Import data_access.py
        data_access_path = os.path.join(base_dir, 'models', 'data_access.py')
        if os.path.exists(data_access_path):
            logger.debug(f"Importing data_access.py from {data_access_path}")
            spec = importlib.util.spec_from_file_location("models.data_access", data_access_path)
            data_access_module = importlib.util.module_from_spec(spec)
            sys.modules['models.data_access'] = data_access_module
            spec.loader.exec_module(data_access_module)
            logger.debug("Successfully imported models.data_access")
        else:
            logger.error(f"data_access.py not found at {data_access_path}")
    except Exception as e:
        logger.error(f"Error initializing models package: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Initialize the views package
    try:
        # Create the views package if it doesn't exist
        if 'views' not in sys.modules:
            logger.debug("Creating views package")
            views_module = importlib.util.module_from_name("views")
            sys.modules['views'] = views_module
        
        # Define all view module paths
        view_modules = {
            'main_window': os.path.join(base_dir, 'views', 'main_window.py'),
            'login_dialog': os.path.join(base_dir, 'views', 'login_dialog.py'),
            'register_dialog': os.path.join(base_dir, 'views', 'register_dialog.py'),
            'dashboard_view': os.path.join(base_dir, 'views', 'dashboard_view.py'),
            'appointments_view': os.path.join(base_dir, 'views', 'appointments_view.py'),
            'patients_view': os.path.join(base_dir, 'views', 'patients_view.py'),
            'settings_view': os.path.join(base_dir, 'views', 'settings_view.py'),
        }
        
        # Import all view modules
        for module_name, module_path in view_modules.items():
            if os.path.exists(module_path):
                logger.debug(f"Importing {module_name} from {module_path}")
                spec = importlib.util.spec_from_file_location(f"views.{module_name}", module_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[f'views.{module_name}'] = module
                
                # Try to execute the module
                try:
                    spec.loader.exec_module(module)
                    logger.debug(f"Successfully imported views.{module_name}")
                except Exception as e:
                    logger.error(f"Error executing module views.{module_name}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.error(f"{module_name}.py not found at {module_path}")
        
        # Import the views package to initialize it
        try:
            import views
            logger.debug("Successfully imported views package")
        except Exception as e:
            logger.error(f"Error importing views package: {e}")
    except Exception as e:
        logger.error(f"Error initializing views package: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Initialize the utils package
    try:
        # Create the utils package if it doesn't exist
        if 'utils' not in sys.modules:
            logger.debug("Creating utils package")
            utils_module = importlib.util.module_from_name("utils")
            sys.modules['utils'] = utils_module
        
        # Import database.py
        database_path = os.path.join(base_dir, 'utils', 'database.py')
        if os.path.exists(database_path):
            logger.debug(f"Importing database.py from {database_path}")
            spec = importlib.util.spec_from_file_location("utils.database", database_path)
            database_module = importlib.util.module_from_spec(spec)
            sys.modules['utils.database'] = database_module
            spec.loader.exec_module(database_module)
            logger.debug("Successfully imported utils.database")
        else:
            logger.error(f"database.py not found at {database_path}")
    except Exception as e:
        logger.error(f"Error initializing utils package: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.debug("Package initialization completed")

# Create a module_from_name function since it's not in importlib.util
def importlib_util_module_from_name(name):
    """Create a new empty module with the given name."""
    import types
    return types.ModuleType(name)

# Add the function to importlib.util if it doesn't exist
if not hasattr(importlib.util, 'module_from_name'):
    importlib.util.module_from_name = importlib_util_module_from_name

# Run the initialization when this script is imported
init_packages()
