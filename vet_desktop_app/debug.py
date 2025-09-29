#!/usr/bin/env python3
"""
Debug script for the ePetCare Vet Desktop application.
This script checks for common issues and helps diagnose problems.
"""

import os
import sys
import importlib
import sqlite3
import traceback


def print_header(text):
    """Print a header with the given text."""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)


def check_python_version():
    """Check the Python version."""
    print_header("Python Version")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    if sys.version_info < (3, 8):
        print("WARNING: Python version is less than 3.8. Some features may not work.")
    else:
        print("Python version is OK.")


def check_python_path():
    """Check the Python path."""
    print_header("Python Path")
    print("PYTHONPATH environment variable:")
    pythonpath = os.environ.get('PYTHONPATH', '')
    if pythonpath:
        for path in pythonpath.split(os.pathsep):
            print(f"  - {path}")
    else:
        print("  Not set")
    
    print("\nsys.path:")
    for path in sys.path:
        print(f"  - {path}")
    
    # Check if current directory is in path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir in sys.path:
        print(f"\nCurrent directory ({current_dir}) is in sys.path.")
    else:
        print(f"\nWARNING: Current directory ({current_dir}) is NOT in sys.path.")
        print("This may cause import errors.")


def check_required_modules():
    """Check if required modules can be imported."""
    print_header("Required Modules")
    
    modules = [
        # Core Python modules
        'os', 'sys', 'json', 'sqlite3', 'datetime', 'pathlib',
        
        # PySide6 modules
        'PySide6', 'PySide6.QtWidgets', 'PySide6.QtCore', 'PySide6.QtGui',
        
        # Application modules
        'views', 'views.main_window', 'views.login_dialog',
        'utils', 'utils.database', 'utils.config',
        'models', 'models.data_access'
    ]
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ {module_name:<30} - OK")
        except ImportError as e:
            print(f"✗ {module_name:<30} - FAILED: {str(e)}")
            if module_name.startswith(('views', 'utils', 'models', 'controllers')):
                print(f"  This is an application module. Make sure the current directory is in sys.path.")


def check_database():
    """Check the PostgreSQL database connection."""
    print_header("PostgreSQL Database")
    
    # Try to find config.json
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    if os.path.exists(config_path):
        print(f"Config file found: {config_path}")
        try:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            pg_config = config.get('postgres', {})
            if pg_config:
                print("PostgreSQL configuration found:")
                # Print the configuration (redacting password)
                safe_config = pg_config.copy()
                if 'password' in safe_config:
                    safe_config['password'] = '********'
                if 'database_url' in safe_config:
                    url = safe_config['database_url']
                    # Replace password in URL with *** if present
                    if url and '://' in url:
                        import re
                        safe_config['database_url'] = re.sub(r'(://[^:]+:)[^@]+(@)', r'\1********\2', url)
                
                for key, value in safe_config.items():
                    if key not in ('password', 'database_url'):  # Skip displaying actual secrets
                        print(f"  - {key}: {value}")
                
                # Try to connect to PostgreSQL
                try:
                    import psycopg2
                    from psycopg2 import sql
                    
                    # Create connection
                    conn_params = {}
                    for key in ('host', 'port', 'database', 'user', 'password'):
                        if key in pg_config:
                            conn_params[key] = pg_config[key]
                    
                    print(f"Attempting to connect to PostgreSQL at {conn_params.get('host')}:{conn_params.get('port')}...")
                    conn = psycopg2.connect(**conn_params)
                    print("✓ Connection successful")
                    
                    # Check for some important tables
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                        tables = cursor.fetchall()
                        print(f"Database contains {len(tables)} tables in public schema")
                        
                        # Check for core tables
                        core_tables = ['auth_user', 'clinic_owner', 'clinic_pet', 'clinic_appointment']
                        for table in core_tables:
                            cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)", (table,))
                            exists = cursor.fetchone()[0]
                            print(f"  {'✓' if exists else '✗'} {table}")
                    
                    conn.close()
                    print("Connection closed properly")
                    
                except ImportError:
                    print("✗ Could not import psycopg2. Please install it with: pip install psycopg2-binary")
                except Exception as e:
                    print(f"✗ Error connecting to PostgreSQL: {str(e)}")
            else:
                print("✗ PostgreSQL configuration not found in config.json")
        except Exception as e:
            print(f"Error reading config: {str(e)}")
    else:
        print(f"✗ Config file not found at {config_path}")


def check_resource_files():
    """Check if resource files exist."""
    print_header("Resource Files")
    
    resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    if os.path.exists(resources_dir):
        print(f"Resources directory exists: {resources_dir}")
        
        # Check for style.qss
        style_path = os.path.join(resources_dir, 'style.qss')
        if os.path.exists(style_path):
            print(f"Style file exists: {style_path}")
        else:
            print(f"WARNING: Style file not found: {style_path}")
        
        # Check for icons
        icons = ['app-icon.png', 'app-icon.ico', 'refresh-icon.png', 'dashboard-icon.png', 
                'patients-icon.png', 'appointments-icon.png', 'settings-icon.png']
        
        print("\nChecking for icon files:")
        for icon in icons:
            icon_path = os.path.join(resources_dir, icon)
            if os.path.exists(icon_path):
                print(f"  ✓ {icon} - EXISTS")
            else:
                print(f"  ✗ {icon} - NOT FOUND")
    else:
        print(f"WARNING: Resources directory not found: {resources_dir}")


def main():
    """Main entry point."""
    print_header("ePetCare Vet Desktop - Debug Information")
    print(f"Current directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    try:
        check_python_version()
        check_python_path()
        check_required_modules()
        check_database()
        check_resource_files()
        
        print_header("Debug Complete")
        print("If you're still experiencing issues, please check the error messages above.")
        print("You can also try running the application with:")
        print("  python -m views.main_window")
        print("Or check specific module imports with:")
        print("  python -c \"import views.main_window; print('Import successful')\"")
        
    except Exception as e:
        print_header("Error During Debug")
        print(f"An error occurred during debugging: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
