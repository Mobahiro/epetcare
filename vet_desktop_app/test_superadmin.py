"""
Test script to verify superadmin dashboard imports
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    
    # Test superadmin dashboard import
    from views.superadmin_dashboard import SuperadminDashboard
    print("✓ SuperadminDashboard imported successfully")
    
    # Test data access imports
    from models.data_access import UserDataAccess, VeterinarianDataAccess, OwnerDataAccess
    print("✓ Data access classes imported successfully")
    
    # Test database connection
    from utils.pg_db import get_connection
    print("✓ Database connection function imported successfully")
    
    print("\n✅ All imports successful! Desktop app is ready.")
    
except Exception as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
