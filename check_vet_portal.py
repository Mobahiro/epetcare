#!/usr/bin/env python3
"""
ePetCare Vet Portal System Check

This script checks for common issues with the ePetCare Vet Portal setup.
"""

import os
import sys
import json
import sqlite3
import importlib

def print_header(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def check_python():
    """Check Python version and installation"""
    print_header("Python Installation")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Check if Python version is 3.8 or higher
    major, minor, *_ = sys.version_info
    if major >= 3 and minor >= 8:
        print("✓ Python version is OK (3.8 or higher)")
    else:
        print("✗ Python version is too old (requires 3.8 or higher)")
    
    # Check if pip is installed
    try:
        import pip
        print(f"✓ pip is installed (version {pip.__version__})")
    except ImportError:
        print("✗ pip is not installed")

def check_directories():
    """Check if required directories exist"""
    print_header("Directory Structure")
    
    # Get the current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check if vet_desktop_app directory exists
    vet_desktop_app_dir = os.path.join(current_dir, "vet_desktop_app")
    if os.path.isdir(vet_desktop_app_dir):
        print(f"✓ vet_desktop_app directory found: {vet_desktop_app_dir}")
    else:
        print(f"✗ vet_desktop_app directory not found: {vet_desktop_app_dir}")
        return
    
    # Check for essential files
    essential_files = [
        "main.py",
        "utils/database.py",
        "utils/db_sync.py",
        "models/data_access.py",
        "views/main_window.py"
    ]
    
    for file in essential_files:
        file_path = os.path.join(vet_desktop_app_dir, file)
        if os.path.isfile(file_path):
            print(f"✓ Essential file found: {file}")
        else:
            print(f"✗ Essential file missing: {file}")
    
    # Check for config.json
    config_path = os.path.join(vet_desktop_app_dir, "config.json")
    if os.path.isfile(config_path):
        print(f"✓ Configuration file found: {config_path}")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            print(f"  - Database path: {config.get('database', {}).get('path', 'Not set')}")
            print(f"  - Real-time sync: {config.get('database', {}).get('real_time_sync', False)}")
        except json.JSONDecodeError:
            print("✗ Configuration file is not valid JSON")
    else:
        print(f"✗ Configuration file not found: {config_path}")

def check_database():
    """Check if the database exists and is accessible"""
    print_header("Database")
    
    # Check for database in root directory
    current_dir = os.getcwd()
    db_path = os.path.join(current_dir, "db.sqlite3")
    
    if os.path.isfile(db_path):
        print(f"✓ Database found in root directory: {db_path}")
        
        # Check if the database is a valid SQLite database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            print(f"✓ Database is a valid SQLite database with {len(tables)} tables")
            print("  Tables found:")
            for table in sorted(tables):
                print(f"  - {table}")
            
            # Check for essential tables
            essential_tables = [
                "auth_user",
                "clinic_owner", 
                "clinic_pet", 
                "clinic_appointment",
                "vet_veterinarian"
            ]
            
            missing_tables = [table for table in essential_tables if table not in tables]
            if missing_tables:
                print("✗ Some essential tables are missing:")
                for table in missing_tables:
                    print(f"  - {table}")
            else:
                print("✓ All essential tables are present")
                
        except sqlite3.Error as e:
            print(f"✗ Error accessing database: {e}")
    else:
        print(f"✗ Database not found in root directory: {db_path}")
        
        # Check for database in vet_desktop_app/data directory
        data_db_path = os.path.join(current_dir, "vet_desktop_app", "data", "db.sqlite3")
        if os.path.isfile(data_db_path):
            print(f"✓ Database found in vet_desktop_app/data directory: {data_db_path}")
        else:
            print(f"✗ Database not found in vet_desktop_app/data directory: {data_db_path}")

def check_dependencies():
    """Check if required Python packages are installed"""
    print_header("Python Dependencies")
    
    required_packages = [
        "PySide6",
        "Pillow"
    ]
    
    for package in required_packages:
        try:
            module = importlib.import_module(package)
            if hasattr(module, "__version__"):
                print(f"✓ {package} is installed (version {module.__version__})")
            else:
                print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is not installed")

def main():
    """Main function"""
    print_header("ePetCare Vet Portal System Check")
    
    check_python()
    check_directories()
    check_database()
    check_dependencies()
    
    print("\nSystem check completed. If any issues were found, please fix them and try again.")
    print("Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()
