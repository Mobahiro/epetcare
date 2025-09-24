#!/usr/bin/env python3
"""
Test script to debug the main application
"""

import sys
import os
import traceback

print("=== DEBUGGING ePetCare Vet Portal ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Add paths
root_dir = os.getcwd()
app_dir = os.path.join(root_dir, 'vet_desktop_app')
sys.path.insert(0, root_dir)
sys.path.insert(0, app_dir)

print(f"Root directory: {root_dir}")
print(f"App directory: {app_dir}")
print(f"Python path: {sys.path[:3]}")

# Change to app directory
os.chdir(app_dir)
print(f"Changed to: {os.getcwd()}")

try:
    print("\n=== Testing imports ===")
    
    print("1. Testing PySide6...")
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QFont
    print("   ✓ PySide6 imports successful")
    
    print("2. Testing application modules...")
    import views
    import utils
    import models
    print("   ✓ Top-level packages imported")
    
    print("3. Testing specific modules...")
    from views.main_window import MainWindow
    print("   ✓ MainWindow imported")
    
    from utils.database import setup_database_connection
    print("   ✓ Database utils imported")
    
    from utils.config import load_config
    print("   ✓ Config utils imported")
    
    print("\n=== Testing application creation ===")
    
    print("4. Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("ePetCare Vet Desktop")
    app.setOrganizationName("ePetCare")
    app.setOrganizationDomain("epetcare.local")
    print("   ✓ QApplication created")
    
    print("5. Loading configuration...")
    config = load_config()
    print(f"   ✓ Configuration loaded: {config}")
    
    print("6. Setting up database...")
    db_path = config.get('database', {}).get('path', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3'))
    print(f"   Database path: {db_path}")
    
    connection_result = setup_database_connection(db_path)
    if not connection_result:
        print("   ✗ Database connection failed")
        sys.exit(1)
    print("   ✓ Database connection successful")
    
    print("7. Creating MainWindow...")
    window = MainWindow()
    print("   ✓ MainWindow created")
    
    print("8. Showing window...")
    window.show()
    print("   ✓ Window shown")
    
    print("\n=== Application ready! ===")
    print("The application window should now be visible.")
    print("Press Ctrl+C to exit or close the window.")
    
    # Start the event loop
    app.exec()
    
except Exception as e:
    print(f"\n=== ERROR OCCURRED ===")
    print(f"Error: {e}")
    print(f"Type: {type(e).__name__}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    # Try to show error in GUI if possible
    try:
        if 'app' in locals():
            QMessageBox.critical(None, "Debug Error", f"Error: {e}\n\nCheck console for details.")
        else:
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "Debug Error", f"Error: {e}\n\nCheck console for details.")
    except:
        pass
    
    input("\nPress Enter to exit...")
    sys.exit(1)
