"""
Database Sync Helper for ePetCare Vet Desktop Application.

This script helps manage the synchronization between the local database
and the remote PostgreSQL database hosted on Render.

Usage:
    python db_sync_helper.py [command]

Commands:
    status      - Show connection status and sync information
    sync        - Force synchronization with the remote database
    upload      - Upload local changes to the remote database
    download    - Download the remote database
    configure   - Update the configuration settings
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
import traceback

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('epetcare_sync')

def get_paths():
    """Get the important paths for the application."""
    # Get the root directory (epetcare)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir.endswith('vet_desktop_app'):
        root_dir = os.path.dirname(current_dir)
    else:
        root_dir = current_dir
    
    # Set up paths
    vet_app_dir = os.path.join(root_dir, 'vet_desktop_app')
    config_path = os.path.join(vet_app_dir, 'config.json')
    
    return {
        'root_dir': root_dir,
        'vet_app_dir': vet_app_dir,
        'config_path': config_path
    }

def load_config(config_path):
    """Load the application configuration."""
    logger.debug(f"Loading configuration from {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.debug("Configuration loaded successfully")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def save_config(config_path, config):
    """Save the application configuration."""
    logger.debug(f"Saving configuration to {config_path}")
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            logger.debug("Configuration saved successfully")
            return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def check_status(config):
    """Check the status of the database connection."""
    logger.info("Checking database connection status...")
    
    remote_db_config = config.get('remote_database', {})
    remote_enabled = remote_db_config.get('enabled', False)
    
    if not remote_enabled:
        logger.info("Remote database is not enabled in the configuration")
        return False
    
    remote_url = remote_db_config.get('url')
    if not remote_url:
        logger.info("Remote database URL is not configured")
        return False
    
    logger.info(f"Remote database URL: {remote_url}")
    logger.info(f"Remote sync interval: {remote_db_config.get('sync_interval', 30)} seconds")
    logger.info(f"Auto sync: {'Enabled' if remote_db_config.get('auto_sync', True) else 'Disabled'}")
    
    # Import the required modules
    try:
        sys.path.insert(0, get_paths()['vet_app_dir'])
        sys.path.insert(0, get_paths()['root_dir'])
        
        from utils.remote_db_client import RemoteDatabaseClient
        logger.debug("Successfully imported RemoteDatabaseClient")
    except ImportError as e:
        logger.error(f"Error importing RemoteDatabaseClient: {e}")
        return False
    
    # Create a remote database client
    remote_client = RemoteDatabaseClient()
    
    # Set up the client
    username = remote_db_config.get('username')
    password = remote_db_config.get('password')
    token = remote_db_config.get('token')
    
    logger.debug(f"Setting up remote database client for URL: {remote_url}")
    success = remote_client.setup(
        base_url=remote_url,
        username=username,
        password=password,
        token=token
    )
    
    if not success:
        logger.error("Failed to set up remote database client")
        return False
    
    logger.info("Remote database client set up successfully")
    
    # Get database info
    logger.info("Getting database information...")
    db_info = remote_client.get_database_info()
    
    if db_info:
        logger.info("Database information retrieved successfully")
        logger.info(f"Timestamp: {db_info.get('timestamp')}")
        logger.info(f"Last sync: {db_info.get('last_sync')}")
        logger.info(f"Database type: {db_info.get('db_type')}")
        logger.info(f"Sync method: {db_info.get('sync_method')}")
        
        tables = db_info.get('tables', [])
        if tables:
            logger.info(f"Tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
        
        return True
    else:
        logger.error("Failed to get database information")
        return False

def force_sync(config):
    """Force synchronization with the remote database."""
    logger.info("Forcing synchronization with remote database...")
    
    remote_db_config = config.get('remote_database', {})
    remote_enabled = remote_db_config.get('enabled', False)
    
    if not remote_enabled:
        logger.error("Remote database is not enabled in the configuration")
        return False
    
    # Import the required modules
    try:
        sys.path.insert(0, get_paths()['vet_app_dir'])
        sys.path.insert(0, get_paths()['root_dir'])
        
        from utils.remote_db_client import RemoteDatabaseClient
        from utils.db_sync import DatabaseSyncManager
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        return False
    
    # Create a remote database client
    remote_client = RemoteDatabaseClient()
    
    # Set up the client
    remote_url = remote_db_config.get('url')
    username = remote_db_config.get('username')
    password = remote_db_config.get('password')
    token = remote_db_config.get('token')
    
    success = remote_client.setup(
        base_url=remote_url,
        username=username,
        password=password,
        token=token
    )
    
    if not success:
        logger.error("Failed to set up remote database client")
        return False
    
    # Download the database
    logger.info("Downloading database from remote server...")
    local_path = os.path.join(get_paths()['vet_app_dir'], 'data', 'db.sqlite3')
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    result = remote_client.download_database(local_path)
    
    if result:
        logger.info(f"Database downloaded successfully to {local_path}")
        return True
    else:
        logger.error("Failed to download database")
        return False

def upload_changes(config):
    """Upload local changes to the remote database."""
    logger.info("Uploading local changes to remote database...")
    
    remote_db_config = config.get('remote_database', {})
    remote_enabled = remote_db_config.get('enabled', False)
    
    if not remote_enabled:
        logger.error("Remote database is not enabled in the configuration")
        return False
    
    # Import the required modules
    try:
        sys.path.insert(0, get_paths()['vet_app_dir'])
        sys.path.insert(0, get_paths()['root_dir'])
        
        from utils.remote_db_client import RemoteDatabaseClient
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        return False
    
    # Create a remote database client
    remote_client = RemoteDatabaseClient()
    
    # Set up the client
    remote_url = remote_db_config.get('url')
    username = remote_db_config.get('username')
    password = remote_db_config.get('password')
    token = remote_db_config.get('token')
    
    success = remote_client.setup(
        base_url=remote_url,
        username=username,
        password=password,
        token=token
    )
    
    if not success:
        logger.error("Failed to set up remote database client")
        return False
    
    # Upload the database
    logger.info("Uploading database to remote server...")
    local_path = os.path.join(get_paths()['vet_app_dir'], 'data', 'db.sqlite3')
    
    if not os.path.exists(local_path):
        logger.error(f"Local database file not found at {local_path}")
        return False
    
    result = remote_client.upload_database(local_path)
    
    if result:
        logger.info(f"Database uploaded successfully from {local_path}")
        return True
    else:
        logger.error("Failed to upload database")
        return False

def download_database(config):
    """Download the remote database."""
    logger.info("Downloading remote database...")
    
    remote_db_config = config.get('remote_database', {})
    remote_enabled = remote_db_config.get('enabled', False)
    
    if not remote_enabled:
        logger.error("Remote database is not enabled in the configuration")
        return False
    
    # Import the required modules
    try:
        sys.path.insert(0, get_paths()['vet_app_dir'])
        sys.path.insert(0, get_paths()['root_dir'])
        
        from utils.remote_db_client import RemoteDatabaseClient
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        return False
    
    # Create a remote database client
    remote_client = RemoteDatabaseClient()
    
    # Set up the client
    remote_url = remote_db_config.get('url')
    username = remote_db_config.get('username')
    password = remote_db_config.get('password')
    token = remote_db_config.get('token')
    
    success = remote_client.setup(
        base_url=remote_url,
        username=username,
        password=password,
        token=token
    )
    
    if not success:
        logger.error("Failed to set up remote database client")
        return False
    
    # Download the database
    logger.info("Downloading database from remote server...")
    local_path = os.path.join(get_paths()['vet_app_dir'], 'data', 'db.sqlite3')
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    result = remote_client.download_database(local_path)
    
    if result:
        logger.info(f"Database downloaded successfully to {local_path}")
        return True
    else:
        logger.error("Failed to download database")
        return False

def configure(config_path, config):
    """Update the configuration settings."""
    logger.info("Updating configuration settings...")
    
    # Get the current configuration
    remote_db_config = config.get('remote_database', {})
    
    # Ask for the configuration values
    print("\nCurrent configuration:")
    print(f"Remote database enabled: {remote_db_config.get('enabled', False)}")
    print(f"Remote database URL: {remote_db_config.get('url', '')}")
    print(f"Username: {remote_db_config.get('username', '')}")
    print(f"Password: {'*' * len(remote_db_config.get('password', ''))}")
    print(f"Sync interval: {remote_db_config.get('sync_interval', 30)} seconds")
    print(f"Auto sync: {remote_db_config.get('auto_sync', True)}")
    
    print("\nEnter new values (leave blank to keep current value):")
    
    # Remote database enabled
    enabled_input = input(f"Enable remote database (y/n) [{remote_db_config.get('enabled', False)}]: ").strip()
    if enabled_input:
        remote_db_config['enabled'] = enabled_input.lower() == 'y'
    
    # Remote database URL
    url_input = input(f"Remote database URL [{remote_db_config.get('url', '')}]: ").strip()
    if url_input:
        remote_db_config['url'] = url_input
    
    # Username
    username_input = input(f"Username [{remote_db_config.get('username', '')}]: ").strip()
    if username_input:
        remote_db_config['username'] = username_input
    
    # Password
    password_input = input(f"Password [{remote_db_config.get('password', '******')}]: ").strip()
    if password_input:
        remote_db_config['password'] = password_input
    
    # Sync interval
    sync_interval_input = input(f"Sync interval in seconds [{remote_db_config.get('sync_interval', 30)}]: ").strip()
    if sync_interval_input:
        try:
            remote_db_config['sync_interval'] = int(sync_interval_input)
        except ValueError:
            logger.error("Sync interval must be a number")
    
    # Auto sync
    auto_sync_input = input(f"Auto sync (y/n) [{remote_db_config.get('auto_sync', True)}]: ").strip()
    if auto_sync_input:
        remote_db_config['auto_sync'] = auto_sync_input.lower() == 'y'
    
    # Update the configuration
    config['remote_database'] = remote_db_config
    
    # Save the configuration
    return save_config(config_path, config)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='ePetCare Database Sync Helper')
    parser.add_argument('command', choices=['status', 'sync', 'upload', 'download', 'configure'],
                        help='Command to execute')
    
    args = parser.parse_args()
    
    paths = get_paths()
    config = load_config(paths['config_path'])
    
    if not config:
        sys.exit(1)
    
    if args.command == 'status':
        success = check_status(config)
    elif args.command == 'sync':
        success = force_sync(config)
    elif args.command == 'upload':
        success = upload_changes(config)
    elif args.command == 'download':
        success = download_database(config)
    elif args.command == 'configure':
        success = configure(paths['config_path'], config)
    
    if success:
        logger.info(f"Command '{args.command}' completed successfully")
    else:
        logger.error(f"Command '{args.command}' failed")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)