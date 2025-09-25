"""
ePetCare Render Configuration Validator

This script checks that all necessary configurations are in place for a successful
Render deployment, and suggests fixes for any issues found.
"""

import os
import sys
import re
import yaml
import json
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_status(item, status, message=""):
    """Print a status message with icon."""
    icon = "✅" if status else "❌"
    print(f"{icon} {item}")
    if message:
        print(f"   {message}")

def check_file_exists(file_path, description):
    """Check if a file exists and print status."""
    exists = os.path.isfile(file_path)
    print_status(f"{description} ({file_path})", exists, 
                "" if exists else "File not found")
    return exists

def check_project_files():
    """Check that all necessary project files exist."""
    print_header("Checking Project Files")
    
    files_to_check = [
        ("requirements.txt", "Requirements file"),
        ("Procfile", "Procfile for web server"),
        ("render.yaml", "Render configuration"),
        ("epetcare/settings_production.py", "Production settings"),
        ("vet_desktop_app/config.json", "Desktop app configuration")
    ]
    
    missing_files = []
    for file_path, desc in files_to_check:
        if not check_file_exists(file_path, desc):
            missing_files.append((file_path, desc))
    
    return missing_files

def check_render_yaml():
    """Check the render.yaml file for common issues."""
    print_header("Checking render.yaml Configuration")
    
    try:
        with open("render.yaml", "r") as f:
            render_config = yaml.safe_load(f)
        
        # Check services
        if "services" not in render_config or not render_config["services"]:
            print_status("Services defined", False, "No services found in render.yaml")
            return False
        
        # Check web service
        web_service = None
        for service in render_config["services"]:
            if service.get("type") == "web":
                web_service = service
                break
        
        if not web_service:
            print_status("Web service", False, "No web service defined in render.yaml")
            return False
        
        # Check essential web service properties
        print_status("Web service defined", True, f"Name: {web_service.get('name', 'unnamed')}")
        
        essential_props = [
            ("buildCommand", "Build command"),
            ("startCommand", "Start command"),
            ("env", "Environment")
        ]
        
        for prop, desc in essential_props:
            has_prop = prop in web_service
            print_status(desc, has_prop, 
                        web_service.get(prop, "Not defined") if has_prop else "Missing")
        
        # Check environment variables
        env_vars = web_service.get("envVars", [])
        essential_env_vars = ["DJANGO_SETTINGS_MODULE", "SECRET_KEY", "DATABASE_URL"]
        
        print_status("Environment variables", bool(env_vars), 
                    f"Found {len(env_vars)} variables" if env_vars else "No environment variables defined")
        
        for var in essential_env_vars:
            found = any(v.get("key") == var for v in env_vars)
            print_status(f"Environment variable: {var}", found, 
                        "Defined" if found else "Missing")
        
        # Check database
        has_database = "databases" in render_config and render_config["databases"]
        print_status("Database defined", has_database, 
                    f"Found {len(render_config['databases'])} databases" if has_database else "No database defined")
        
        return True
    except FileNotFoundError:
        print_status("render.yaml", False, "File not found")
        return False
    except yaml.YAMLError as e:
        print_status("render.yaml syntax", False, f"Invalid YAML: {e}")
        return False
    except Exception as e:
        print_status("render.yaml processing", False, f"Error: {e}")
        return False

def check_database_configuration():
    """Check database configuration in settings files."""
    print_header("Checking Database Configuration")
    
    try:
        # Check production settings
        has_prod_settings = os.path.isfile("epetcare/settings_production.py")
        print_status("Production settings file", has_prod_settings)
        
        if has_prod_settings:
            with open("epetcare/settings_production.py", "r") as f:
                content = f.read()
            
            # Check for database configuration
            has_dj_database_url = "import dj_database_url" in content
            print_status("dj_database_url import", has_dj_database_url)
            
            has_database_url = "DATABASE_URL" in content
            print_status("DATABASE_URL usage", has_database_url)
            
            has_database_config = "DATABASES =" in content
            print_status("DATABASES configuration", has_database_config)
        
        # Check main settings
        with open("epetcare/settings.py", "r") as f:
            content = f.read()
        
        # Check if SQLite is used in main settings
        uses_sqlite = "sqlite3" in content
        print_status("Development uses SQLite", uses_sqlite)
        
        return has_prod_settings and has_dj_database_url and has_database_url and has_database_config
    except Exception as e:
        print_status("Database configuration check", False, f"Error: {e}")
        return False

def check_api_configuration():
    """Check API configuration for desktop sync."""
    print_header("Checking API Configuration")
    
    try:
        # Check API URLs in vet_portal
        has_api_urls = os.path.isfile("vet_portal/api/urls.py")
        print_status("API URLs file", has_api_urls)
        
        if has_api_urls:
            with open("vet_portal/api/urls.py", "r") as f:
                content = f.read()
            
            # Check for database sync endpoints
            has_sync_endpoint = "database/sync/" in content
            print_status("Database sync endpoint", has_sync_endpoint)
            
            has_download_endpoint = "database/download/" in content
            print_status("Database download endpoint", has_download_endpoint)
            
            has_upload_endpoint = "database/upload/" in content
            print_status("Database upload endpoint", has_upload_endpoint)
        
        # Check desktop app config
        has_desktop_config = os.path.isfile("vet_desktop_app/config.json")
        print_status("Desktop app config file", has_desktop_config)
        
        if has_desktop_config:
            with open("vet_desktop_app/config.json", "r") as f:
                config = json.load(f)
            
            remote_db = config.get("remote_database", {})
            has_remote_db = bool(remote_db)
            print_status("Remote database configuration", has_remote_db)
            
            if has_remote_db:
                url = remote_db.get("url", "")
                print_status("Remote URL defined", bool(url), url if url else "Not defined")
                
                # Check URL format
                if url:
                    has_api_in_url = "/api" in url
                    print_status("URL contains /api", has_api_in_url, 
                                "Correct format" if has_api_in_url else "Should contain '/api'")
                    
                    has_vet_portal_in_url = "/vet_portal/api" in url
                    print_status("URL contains /vet_portal/api", not has_vet_portal_in_url, 
                                "Needs to be updated to '/api'" if has_vet_portal_in_url else "Correct format")
        
        return has_api_urls and has_sync_endpoint and has_download_endpoint and has_upload_endpoint
    except Exception as e:
        print_status("API configuration check", False, f"Error: {e}")
        return False

def check_requirements():
    """Check requirements.txt for necessary packages."""
    print_header("Checking Requirements")
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        essential_packages = [
            "Django", 
            "djangorestframework", 
            "psycopg2", 
            "dj-database-url", 
            "gunicorn"
        ]
        
        for package in essential_packages:
            has_package = re.search(fr"{package}[>=<]", content, re.IGNORECASE) is not None
            print_status(f"Package: {package}", has_package)
        
        return True
    except FileNotFoundError:
        print_status("requirements.txt", False, "File not found")
        return False
    except Exception as e:
        print_status("Requirements check", False, f"Error: {e}")
        return False

def create_missing_files(missing_files):
    """Create templates for missing files."""
    print_header("Creating Missing Files")
    
    for file_path, desc in missing_files:
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Create the file with template content
            if file_path == "Procfile":
                content = "web: gunicorn epetcare.wsgi:application --bind 0.0.0.0:$PORT"
            elif file_path == "requirements.txt":
                content = """# Base Django and REST framework
Django>=5.2.6,<6.0
djangorestframework>=3.14.0

# PostgreSQL support
psycopg2-binary>=2.9.9
dj-database-url>=2.1.0

# Gunicorn for production server
gunicorn>=21.2.0

# Security, needed for HTTPS settings
django-cors-headers>=4.3.0

# Static files
whitenoise>=6.6.0

# Environment variables
python-dotenv>=1.0.0

# For Render deployment
requests>=2.31.0
"""
            elif file_path == "render.yaml":
                content = """# Render configuration file
# This file defines the services for the ePetCare application

services:
  # Web service for the ePetCare Django application
  - type: web
    name: epetcare
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: gunicorn epetcare.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.0
      - key: WEB_CONCURRENCY
        value: 4  # Number of Gunicorn workers
      - key: DJANGO_SETTINGS_MODULE
        value: epetcare.settings_production
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: epetcare_db
          property: connectionString
      - key: ALLOWED_HOST
        sync: false  # Set this manually in Render dashboard

# Database for the application
databases:
  - name: epetcare_db
    databaseName: epetcare
    user: epetcare
    plan: free  # Use the appropriate plan based on your needs
"""
            elif file_path == "epetcare/settings_production.py":
                content = """\"\"\"
Production settings for epetcare project deployed on Render.
These settings override or extend the base settings.py.
\"\"\"

import os
import dj_database_url
from pathlib import Path
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Get the SECRET_KEY from environment variable
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# Allow the Render host domain
ALLOWED_HOSTS = [
    '.onrender.com',  # Render domains
    os.environ.get('ALLOWED_HOST', '*'),  # Custom domain if set up
]

# Use HTTPS for secure cookies and more
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Use PostgreSQL database on Render
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional security settings
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
"""
            else:
                content = "# Template created by Render Configuration Validator\n# Please edit this file with appropriate content\n"
            
            with open(file_path, "w") as f:
                f.write(content)
                
            print_status(f"Created {desc}", True)
        except Exception as e:
            print_status(f"Failed to create {desc}", False, f"Error: {e}")

def fix_desktop_config():
    """Fix the desktop app configuration."""
    print_header("Fixing Desktop App Configuration")
    
    try:
        config_path = "vet_desktop_app/config.json"
        if not os.path.isfile(config_path):
            print_status("Config file", False, "File not found")
            return False
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        remote_db = config.get("remote_database", {})
        
        if not remote_db:
            print_status("Remote database section", False, "Not found in config")
            return False
        
        url = remote_db.get("url", "")
        
        if not url:
            print_status("Remote URL", False, "Not defined in config")
            return False
        
        # Check if URL needs to be fixed
        fixed = False
        new_url = url
        
        if "/vet_portal/api" in url:
            new_url = url.replace("/vet_portal/api", "/api")
            fixed = True
        
        if fixed:
            # Update the URL
            remote_db["url"] = new_url
            config["remote_database"] = remote_db
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
            
            print_status("URL updated", True, f"Changed from {url} to {new_url}")
            return True
        else:
            print_status("URL check", True, "URL format is correct")
            return True
    except Exception as e:
        print_status("Config fix", False, f"Error: {e}")
        return False

def print_recommendations():
    """Print recommendations for deployment."""
    print_header("Recommendations for Successful Render Deployment")
    
    print("""
1. Database Migration:
   - After deployment, you may need to run migrations on Render.
   - Use the Render dashboard to open a shell and run:
     python manage.py migrate
   
2. API URLs:
   - Ensure your desktop app is using the correct API URL format:
     https://epetcare.onrender.com/api
   - Not /vet_portal/api
   
3. Error Handling:
   - Use the fix_render_connection.py script if you encounter database issues
   - Use test_api_connection.py to diagnose API connection problems
   
4. Web Hook:
   - Consider setting up a build hook in your render.yaml
   - This allows you to trigger new deployments from external systems
   
5. Environment Variables:
   - Double-check your environment variables in the Render dashboard
   - Make sure SECRET_KEY is securely generated
   
6. Documentation:
   - Refer to RENDER_CONNECTION_GUIDE.md for troubleshooting
   - Use fix_and_start.bat for a quick guided fix process
   
Useful Render Documentation:
- Python services: https://render.com/docs/deploy-python
- Databases: https://render.com/docs/databases
- Environment variables: https://render.com/docs/environment-variables
    """)

def main():
    print("""
╔════════════════════════════════════════════════════════╗
║            ePetCare Render Configuration               ║
║                      Validator                         ║
╚════════════════════════════════════════════════════════╝
    
This tool checks your project configuration for Render deployment
and helps fix common issues that might cause connection problems.
    """)
    
    # Check project files
    missing_files = check_project_files()
    
    # Check configurations
    render_config_ok = check_render_yaml()
    db_config_ok = check_database_configuration()
    api_config_ok = check_api_configuration()
    requirements_ok = check_requirements()
    
    # Fix issues
    if missing_files:
        print("\nWould you like to create templates for missing files? (y/n)")
        if input().lower() == 'y':
            create_missing_files(missing_files)
    
    print("\nWould you like to fix the desktop app configuration? (y/n)")
    if input().lower() == 'y':
        fix_desktop_config()
    
    # Print recommendations
    print_recommendations()
    
    # Summary
    print_header("Configuration Check Summary")
    print_status("Project files", not missing_files, 
                "All required files present" if not missing_files else f"Missing {len(missing_files)} files")
    print_status("render.yaml configuration", render_config_ok)
    print_status("Database configuration", db_config_ok)
    print_status("API configuration", api_config_ok)
    print_status("Requirements", requirements_ok)
    
    if not missing_files and render_config_ok and db_config_ok and api_config_ok and requirements_ok:
        print("\n✅ Your project appears to be correctly configured for Render deployment!")
    else:
        print("\n⚠️ Some issues were found in your configuration. Please address them before deployment.")
    
    print("\nDone!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")