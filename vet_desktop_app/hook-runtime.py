"""
Runtime hook for PyInstaller to ensure proper module loading.
This script runs before the application starts.
"""

import os
import sys
import importlib.util


def add_to_path(path):
    """Add a directory to sys.path if it's not already there."""
    if path not in sys.path:
        sys.path.insert(0, path)


# Get the directory where the executable is located
# PyInstaller sets sys._MEIPASS, not os._MEIPASS
base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))

# Add the base directory to the path
add_to_path(base_dir)

# Add common module directories to the path
for module_dir in ['views', 'utils', 'models', 'controllers']:
    module_path = os.path.join(base_dir, module_dir)
    if os.path.exists(module_path):
        add_to_path(module_path)

# Print diagnostic information if in debug mode
if os.environ.get('EPETCARE_DEBUG') == '1':
    print(f"Runtime hook executed from: {__file__}")
    print(f"Base directory: {base_dir}")
    print(f"Python path: {sys.path}")
    print(f"Python version: {sys.version}")
    print(f"Executable: {sys.executable}")
    
    # Check if critical modules can be imported
    for module_name in ['views', 'utils', 'models', 'PySide6.QtWidgets']:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                print(f"Module {module_name} found at: {spec.origin}")
            else:
                print(f"Module {module_name} not found!")
        except ImportError as e:
            print(f"Error importing {module_name}: {e}")
