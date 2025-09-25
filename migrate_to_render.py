"""
ePetCare Database Migration to Render

This script helps migrate your local SQLite database to PostgreSQL on Render.
It creates a data dump that can be used for initial setup of your remote database.

Usage:
    python migrate_to_render.py

Requirements:
    - Django
    - PostgreSQL client (psycopg2)
    - dj_database_url
"""

import os
import sys
import json
import django
import subprocess
import tempfile
from datetime import datetime
import requests

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "epetcare.settings")
django.setup()

from django.core.management import call_command
from django.conf import settings
import dj_database_url

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_migration.log')
    ]
)

logger = logging.getLogger(__name__)

def get_render_database_url():
    """Get database URL from Render dashboard or environment"""
    # First try environment variable
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        logger.info("Using DATABASE_URL from environment")
        return database_url
    
    # Try to get it from config
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # This is not the database URL, but we can ask the user to input it
        remote_url = config.get('remote_database', {}).get('url')
        if remote_url:
            logger.info(f"Found Render URL: {remote_url}")
    except:
        logger.warning("Could not read config.json")
    
    # Ask user to input database URL
    print("\nPlease enter your PostgreSQL database URL from Render dashboard.")
    print("It should look like: postgres://username:password@host:port/database_name")
    database_url = input("Database URL: ").strip()
    
    if not database_url:
        logger.error("No database URL provided. Exiting.")
        sys.exit(1)
        
    return database_url

def create_data_dump():
    """Create a JSON dump of the local SQLite database"""
    logger.info("Creating data dump from local database...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_path = f"data_dump_{timestamp}.json"
    
    try:
        # Use Django's dumpdata command to create a JSON dump
        call_command('dumpdata', 
                     exclude=['contenttypes', 'auth.permission', 'sessions'], 
                     indent=2, 
                     output=dump_path)
        
        logger.info(f"Data dump created successfully: {dump_path}")
        return dump_path
    except Exception as e:
        logger.error(f"Failed to create data dump: {e}")
        return None

def apply_migrations_to_remote(database_url):
    """Apply migrations to the remote database"""
    logger.info("Applying migrations to remote database...")
    
    try:
        # Temporarily override database settings
        os.environ['DATABASE_URL'] = database_url
        os.environ['DJANGO_SETTINGS_MODULE'] = 'epetcare.settings_production'
        
        # Apply migrations
        call_command('migrate')
        
        logger.info("Migrations applied successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to apply migrations: {e}")
        return False
    finally:
        # Reset environment
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        os.environ['DJANGO_SETTINGS_MODULE'] = 'epetcare.settings'

def load_data_to_remote(database_url, dump_path):
    """Load data dump to the remote database"""
    logger.info("Loading data to remote database...")
    
    if not dump_path or not os.path.exists(dump_path):
        logger.error("Data dump file not found")
        return False
    
    try:
        # Temporarily override database settings
        os.environ['DATABASE_URL'] = database_url
        os.environ['DJANGO_SETTINGS_MODULE'] = 'epetcare.settings_production'
        
        # Load data
        call_command('loaddata', dump_path)
        
        logger.info("Data loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return False
    finally:
        # Reset environment
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        os.environ['DJANGO_SETTINGS_MODULE'] = 'epetcare.settings'

def push_to_render_api(dump_path):
    """Try to push the data through the Render API"""
    logger.info("Attempting to push data through API...")
    
    config_path = os.path.join('vet_desktop_app', 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        remote_db = config.get('remote_database', {})
        base_url = remote_db.get('url', '')
        username = remote_db.get('username', '')
        password = remote_db.get('password', '')
        
        if not base_url:
            logger.error("Remote database URL not configured")
            return False
        
        if base_url.endswith('/'):
            base_url = base_url[:-1]
            
        # Try different API endpoints
        api_endpoints = [
            f"{base_url}/api/database/upload/",
            f"{base_url}/vet_portal/api/database/upload/",
            f"{base_url}/api/v1/database/upload/"
        ]
        
        for endpoint in api_endpoints:
            try:
                logger.info(f"Trying to upload to {endpoint}")
                
                with open(dump_path, 'rb') as f:
                    files = {'database': f}
                    auth = (username, password) if username and password else None
                    
                    response = requests.post(
                        endpoint, 
                        files=files,
                        auth=auth,
                        timeout=60
                    )
                
                if response.status_code == 200:
                    logger.info("Upload successful")
                    return True
                else:
                    logger.warning(f"Upload failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.warning(f"Error uploading to {endpoint}: {e}")
        
        logger.error("All API upload attempts failed")
        return False
    except Exception as e:
        logger.error(f"Error in API upload: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("ePetCare Database Migration to Render".center(60))
    print("="*60 + "\n")
    
    print("This script will help you migrate your local SQLite database to Render's PostgreSQL.\n")
    print("Steps:")
    print("1. Create a data dump from your local database")
    print("2. Apply migrations to the remote PostgreSQL database")
    print("3. Load the data to the remote database")
    print("4. Update your GitHub repository (optional)\n")
    
    # Create data dump
    dump_path = create_data_dump()
    if not dump_path:
        print("\nFailed to create data dump. Check the log for details.")
        return
    
    # Ask for database URL
    database_url = get_render_database_url()
    
    # Apply migrations
    print("\nApplying migrations to the remote database...")
    if not apply_migrations_to_remote(database_url):
        print("\nFailed to apply migrations. Check the log for details.")
        
        # Try alternate method
        print("\nTrying to push data through API...")
        if push_to_render_api(dump_path):
            print("\nData successfully pushed through API!")
        else:
            print("\nFailed to push data through API. Check the log for details.")
        
        return
    
    # Load data
    print("\nLoading data to the remote database...")
    if load_data_to_remote(database_url, dump_path):
        print("\nData loaded successfully!")
    else:
        print("\nFailed to load data. Check the log for details.")
        
        # Try alternate method
        print("\nTrying to push data through API...")
        if push_to_render_api(dump_path):
            print("\nData successfully pushed through API!")
        else:
            print("\nFailed to push data through API. Check the log for details.")
    
    # GitHub update reminder
    print("\nDon't forget to push your changes to GitHub!")
    print("Your Render deployment will automatically update when you push to the main branch.")
    
    print("\nMigration process completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        logger.exception("Unhandled exception")
        print(f"\nAn error occurred: {e}")
        print("Check the log file for details: db_migration.log")