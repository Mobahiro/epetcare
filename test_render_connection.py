"""
Test script to verify the connection to the PostgreSQL database on Render
from the local vet desktop application.

Usage:
    python test_render_connection.py

This script will attempt to connect to your Render PostgreSQL database and 
verify that data changes reflect in real-time.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('epetcare_test')

def main():
    """Main function to test the database connection."""
    logger.info("Starting Render PostgreSQL connection test")
    
    # Get the root directory (epetcare)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir.endswith('vet_desktop_app'):
        root_dir = os.path.dirname(current_dir)
    else:
        root_dir = current_dir
    
    # Set up paths
    vet_app_dir = os.path.join(root_dir, 'vet_desktop_app')
    config_path = os.path.join(vet_app_dir, 'config.json')
    
    # Check if the vet_desktop_app directory exists
    if not os.path.exists(vet_app_dir):
        logger.error(f"Vet desktop app directory not found at {vet_app_dir}")
        sys.exit(1)
    
    # Add the vet_desktop_app directory to the Python path
    sys.path.insert(0, vet_app_dir)
    sys.path.insert(0, root_dir)
    
    # Load the configuration
    logger.info(f"Loading configuration from {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Check if remote database is configured
    remote_db_config = config.get('remote_database', {})
    if not remote_db_config.get('enabled'):
        logger.error("Remote database is not enabled in the configuration")
        logger.error("Please set 'enabled' to true in the 'remote_database' section of config.json")
        sys.exit(1)
    
    remote_url = remote_db_config.get('url')
    if not remote_url:
        logger.error("Remote database URL is not configured")
        logger.error("Please set 'url' in the 'remote_database' section of config.json")
        sys.exit(1)
    
    logger.info(f"Remote database URL: {remote_url}")
    
    # Import the required modules
    try:
        from utils.remote_db_client import RemoteDatabaseClient
        logger.info("Successfully imported RemoteDatabaseClient")
    except ImportError as e:
        logger.error(f"Error importing RemoteDatabaseClient: {e}")
        sys.exit(1)
    
    # Create a remote database client
    remote_client = RemoteDatabaseClient()
    
    # Set up the client
    username = remote_db_config.get('username')
    password = remote_db_config.get('password')
    token = remote_db_config.get('token')
    
    logger.info(f"Setting up remote database client for URL: {remote_url}")
    success = remote_client.setup(
        base_url=remote_url,
        username=username,
        password=password,
        token=token
    )
    
    if not success:
        logger.error("Failed to set up remote database client")
        sys.exit(1)
    
    logger.info("Remote database client set up successfully")
    
    # Get database info
    logger.info("Getting database information...")
    db_info = remote_client.get_database_info()
    
    if db_info:
        logger.info("Database information retrieved successfully")
        logger.info(f"Database info: {json.dumps(db_info, indent=4)}")
    else:
        logger.error("Failed to get database information")
        sys.exit(1)
    
    # Try to download the database
    logger.info("Testing database download...")
    local_path = remote_client.download_database()
    
    if local_path:
        logger.info(f"Database downloaded successfully to {local_path}")
        
        # Check the database file
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            logger.info(f"Database file exists and is not empty: {os.path.getsize(local_path)} bytes")
            
            # Try to open the database
            try:
                import sqlite3
                conn = sqlite3.connect(local_path)
                cursor = conn.cursor()
                
                # Get the list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
                
                logger.info(f"Tables found in the database: {', '.join(tables)}")
                
                # Check some data
                if 'auth_user' in tables:
                    cursor.execute("SELECT COUNT(*) FROM auth_user")
                    count = cursor.fetchone()[0]
                    logger.info(f"Number of users in the database: {count}")
                
                if 'clinic_pet' in tables:
                    cursor.execute("SELECT COUNT(*) FROM clinic_pet")
                    count = cursor.fetchone()[0]
                    logger.info(f"Number of pets in the database: {count}")
                
                conn.close()
                logger.info("Database opened and accessed successfully")
            except Exception as e:
                logger.error(f"Error opening the database: {e}")
        else:
            logger.error(f"Database file is empty or does not exist: {local_path}")
    else:
        logger.error("Failed to download database")
        logger.error("This could be due to authentication issues or the database being served via API only")
    
    logger.info("Test completed")


if __name__ == "__main__":
    main()