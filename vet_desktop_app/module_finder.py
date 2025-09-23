"""
Module finder script for the ePetCare Vet Desktop application.
This script helps locate modules at runtime, especially when running as a PyInstaller package.
"""

import os
import sys
import importlib
import logging
import traceback

logger = logging.getLogger('epetcare')

def find_module(module_name):
    """
    Attempts to find and import a module.
    Returns True if successful, False otherwise.
    """
    try:
        importlib.import_module(module_name)
        logger.debug(f"Successfully imported module: {module_name}")
        return True
    except ImportError as e:
        logger.error(f"Failed to import module: {module_name} - {e}")
        return False

def ensure_modules_importable():
    """
    Ensures that all required modules can be imported.
    Adjusts Python path if necessary.
    """
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller executable
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        logger.debug(f"Running as frozen application. Base directory: {base_dir}")
    else:
        # Running as a normal Python script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logger.debug(f"Running as script. Base directory: {base_dir}")
    
    # Add the base directory to the path if not already there
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
        logger.debug(f"Added {base_dir} to Python path")
    
    # Add parent directory to the path if not already there
    parent_dir = os.path.dirname(base_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        logger.debug(f"Added {parent_dir} to Python path")
    
    # Add common module directories to the path
    for module_dir in ['views', 'utils', 'models', 'controllers']:
        module_path = os.path.join(base_dir, module_dir)
        if os.path.exists(module_path) and module_path not in sys.path:
            sys.path.insert(0, module_path)
            logger.debug(f"Added {module_path} to Python path")
    
    # Try to import critical modules
    critical_modules = [
        'models',
        'models.data_access',
        'models.models',
        'views',
        'views.main_window',
        'views.login_dialog',
        'views.register_dialog',
        'utils',
        'utils.database',
        'utils.config',
        'utils.notification_manager'
    ]
    
    # First, try importing the modules normally
    all_imported = all(find_module(module) for module in critical_modules)
    
    if not all_imported:
        logger.warning("Some modules could not be imported. Trying alternative approaches...")
        
        # Create __init__.py files if they don't exist
        for module_dir in ['views', 'utils', 'models', 'controllers']:
            module_path = os.path.join(base_dir, module_dir)
            init_file = os.path.join(module_path, '__init__.py')
            if os.path.exists(module_path) and not os.path.exists(init_file):
                try:
                    with open(init_file, 'w') as f:
                        f.write('# Auto-generated __init__.py file\n')
                    logger.debug(f"Created __init__.py in {module_path}")
                except Exception as e:
                    logger.error(f"Failed to create __init__.py in {module_path}: {e}")
        
        # Try manual imports for each critical module
        for module_name in critical_modules:
            if '.' in module_name:
                # This is a submodule
                package_name, submodule_name = module_name.split('.', 1)
                module_file = f"{submodule_name.replace('.', os.sep)}.py"
                module_path = os.path.join(base_dir, package_name, module_file)
                
                if os.path.exists(module_path):
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        logger.debug(f"Manually loaded {module_name} from {module_path}")
                    except Exception as e:
                        logger.error(f"Failed to manually load {module_name} from {module_path}: {e}")
                        logger.error(traceback.format_exc())
                else:
                    logger.error(f"Module file not found: {module_path}")
            else:
                # This is a top-level package
                package_dir = os.path.join(base_dir, module_name)
                if os.path.exists(package_dir) and os.path.isdir(package_dir):
                    try:
                        # Create a spec for the package
                        spec = importlib.machinery.PathFinder.find_spec(module_name, [base_dir])
                        if spec:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)
                            logger.debug(f"Manually loaded package {module_name} from {package_dir}")
                        else:
                            logger.error(f"Could not find spec for package {module_name}")
                    except Exception as e:
                        logger.error(f"Failed to manually load package {module_name}: {e}")
                        logger.error(traceback.format_exc())
                else:
                    logger.error(f"Package directory not found: {package_dir}")
    
    # Check if we've successfully imported all critical modules
    all_imported = all(module_name in sys.modules for module_name in critical_modules)
    if all_imported:
        logger.info("All critical modules successfully imported")
    else:
        missing = [m for m in critical_modules if m not in sys.modules]
        logger.warning(f"Some modules still missing: {missing}")
    
    return all_imported

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Test module finding
    success = ensure_modules_importable()
    print(f"Module finding {'succeeded' if success else 'failed'}")
    
    # Try to import and use a module
    try:
        from models.data_access import UserDataAccess
        print("Successfully imported UserDataAccess")
    except ImportError as e:
        print(f"Failed to import UserDataAccess: {e}")
