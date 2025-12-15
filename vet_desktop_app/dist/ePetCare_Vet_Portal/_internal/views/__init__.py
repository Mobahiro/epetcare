"""
ePetCare Views Package
"""

# Import views to make them available at the package level
try:
    from . import main_window
    from . import login_dialog
except ImportError as e:
    print(f"Error importing views: {e}")