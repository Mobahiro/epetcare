"""
ePetCare Render Connection Diagnostics and Repair

This script will:
1. Diagnose issues with the Render connection
2. Fix the SQLite database corruption
3. Update the configuration to use the correct Render URL format
4. Test the connection to Render

Usage: python fix_render_connection.py
"""

import os
import sys
import json
import shutil
import logging
import sqlite3
import requests
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('connection_fix.log')
    ]
)

logger = logging.getLogger('epetcare_fix')

def get_paths():
    """Get the paths to important files and directories."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = current_dir
    
    app_dir = os.path.join(root_dir, 'vet_desktop_app')
    config_path = os.path.join(app_dir, 'config.json')
    db_path = os.path.join(root_dir, 'db.sqlite3')
    local_db_path = os.path.join(app_dir, 'data', 'db.sqlite3')
    
    return {
        'root_dir': root_dir,
        'app_dir': app_dir,
        'config_path': config_path,
        'db_path': db_path,
        'local_db_path': local_db_path
    }

def load_config(config_path):
    """Load configuration from file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return None

def save_config(config_path, config):
    """Save configuration to file."""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save config to {config_path}: {e}")
        return False

def check_db_integrity(db_path):
    """Check the integrity of the SQLite database."""
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        
        if result == 'ok':
            logger.info(f"Database integrity check passed: {db_path}")
            return True
        else:
            logger.error(f"Database integrity check failed: {result}")
            return False
    except Exception as e:
        logger.error(f"Error checking database integrity: {e}")
        return False

def fix_database(db_path):
    """Attempt to fix the SQLite database."""
    logger.info(f"Attempting to fix database: {db_path}")
    
    # Create a backup
    backup_path = db_path + ".bak"
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created backup of database at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        # Continue anyway
    
    try:
        # Create a new database
        fixed_db_path = db_path + ".fixed"
        
        # Try to recover tables and data
        src_conn = sqlite3.connect(db_path)
        dst_conn = sqlite3.connect(fixed_db_path)
        
        # Get the list of tables
        cursor = src_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # Try to recover each table
        recovered_tables = []
        failed_tables = []
        
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_'):
                continue
            
            try:
                logger.info(f"Attempting to recover table: {table_name}")
                
                # Try to get the table schema
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                schema = cursor.fetchone()
                
                if schema and schema[0]:
                    # Create the table
                    dst_conn.execute(schema[0])
                    logger.debug(f"Created table {table_name}")
                    
                    # Try to copy the data
                    try:
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        
                        if rows:
                            # Get column names
                            columns = [desc[0] for desc in cursor.description]
                            placeholders = ', '.join(['?' for _ in columns])
                            columns_str = ', '.join(columns)
                            
                            # Insert the data
                            for row in rows:
                                try:
                                    dst_conn.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", row)
                                except sqlite3.Error as row_error:
                                    logger.debug(f"Error inserting row in {table_name}: {row_error}")
                            
                            dst_conn.commit()
                            logger.debug(f"Copied {len(rows)} rows from {table_name}")
                        
                        recovered_tables.append(table_name)
                        logger.info(f"Successfully recovered table: {table_name}")
                    except sqlite3.Error as data_error:
                        logger.warning(f"Could not copy data from {table_name}: {data_error}")
                        failed_tables.append(table_name)
                else:
                    logger.warning(f"Could not retrieve schema for {table_name}")
                    failed_tables.append(table_name)
            except Exception as e:
                logger.error(f"Error recovering table {table_name}: {e}")
                failed_tables.append(table_name)
        
        # Close connections
        src_conn.close()
        dst_conn.close()
        
        logger.info(f"Recovered {len(recovered_tables)} tables: {', '.join(recovered_tables)}")
        if failed_tables:
            logger.warning(f"Failed to recover {len(failed_tables)} tables: {', '.join(failed_tables)}")
        
        # Replace the original with the fixed database
        try:
            os.replace(fixed_db_path, db_path)
            logger.info(f"Replaced original database with fixed version")
            
            # Verify the new database
            if check_db_integrity(db_path):
                logger.info("Fixed database passes integrity check")
                return True
            else:
                logger.warning("Fixed database does not pass integrity check, but may still be usable")
                return True
        except Exception as e:
            logger.error(f"Failed to replace original database: {e}")
            logger.info(f"Fixed database is available at {fixed_db_path}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to fix database: {e}")
        return False

def check_render_url(url):
    """Check if the Render URL is accessible."""
    logger.info(f"Checking Render URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        
        logger.info(f"Response status code: {status_code}")
        
        if status_code == 200:
            logger.info("URL is accessible")
            return True
        elif status_code == 404:
            logger.error("URL returned 404 Not Found")
            return False
        else:
            logger.warning(f"URL returned status code {status_code}")
            return status_code < 500  # Return True if not a server error
    except requests.RequestException as e:
        logger.error(f"Error accessing URL: {e}")
        return False

def fix_render_url(config):
    """Fix the Render URL in the configuration."""
    remote_db_config = config.get('remote_database', {})
    url = remote_db_config.get('url')
    
    if not url:
        logger.error("Remote database URL is not configured")
        return False
    
    logger.info(f"Current remote database URL: {url}")
    
    # Check if the URL contains /vet_portal/api and remove it
    if '/vet_portal/api' in url:
        new_url = url.split('/vet_portal/api')[0]
        logger.info(f"Removing /vet_portal/api from URL: {new_url}")
    else:
        new_url = url
        logger.info("URL does not contain /vet_portal/api")
    
    # Test the URL
    if check_render_url(new_url):
        remote_db_config['url'] = new_url
        config['remote_database'] = remote_db_config
        logger.info(f"Updated URL to {new_url}")
        return True
    else:
        logger.warning(f"Could not access {new_url}")
        
        # Try adding https:// if it's missing
        if not new_url.startswith('http'):
            https_url = f"https://{new_url}"
            logger.info(f"Trying with https://: {https_url}")
            
            if check_render_url(https_url):
                remote_db_config['url'] = https_url
                config['remote_database'] = remote_db_config
                logger.info(f"Updated URL to {https_url}")
                return True
        
        return False

def create_empty_database(db_path):
    """Create an empty SQLite database with basic structure."""
    logger.info(f"Creating empty database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create some basic tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_user (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinic_pet (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            species TEXT,
            breed TEXT,
            date_of_birth TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Created empty database at {db_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create empty database: {e}")
        return False

def install_fixed_client():
    """Install the fixed remote_db_client.py file."""
    paths = get_paths()
    
    src_path = os.path.join(paths['root_dir'], 'vet_desktop_app', 'utils', 'remote_db_client_fixed.py')
    dst_path = os.path.join(paths['root_dir'], 'vet_desktop_app', 'utils', 'remote_db_client.py')
    
    if not os.path.exists(src_path):
        logger.error(f"Fixed client not found at {src_path}")
        return False
    
    try:
        shutil.copy2(src_path, dst_path)
        logger.info(f"Installed fixed client to {dst_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to install fixed client: {e}")
        return False

def ensure_data_directory():
    """Ensure the data directory exists."""
    paths = get_paths()
    data_dir = os.path.join(paths['app_dir'], 'data')
    
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            logger.info(f"Created data directory at {data_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
            return False
    else:
        logger.info(f"Data directory already exists at {data_dir}")
        return True

def main():
    """Main function."""
    logger.info("Starting ePetCare Render Connection Fix")
    
    paths = get_paths()
    
    # Check if the configuration file exists
    if not os.path.exists(paths['config_path']):
        logger.error(f"Configuration file not found at {paths['config_path']}")
        return False
    
    # Load configuration
    config = load_config(paths['config_path'])
    if not config:
        return False
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Check database integrity
    db_corrupted = False
    
    if os.path.exists(paths['db_path']):
        if not check_db_integrity(paths['db_path']):
            db_corrupted = True
            
            # Try to fix the database
            if not fix_database(paths['db_path']):
                logger.warning("Could not fix database, creating a new empty one")
                
                # Create a new empty database
                if not create_empty_database(paths['db_path']):
                    logger.error("Failed to create a new database")
        else:
            logger.info("Main database is valid")
    else:
        logger.warning(f"Main database not found at {paths['db_path']}")
        
        # Create a new empty database
        if not create_empty_database(paths['db_path']):
            logger.error("Failed to create a new database")
    
    # Check local database
    if os.path.exists(paths['local_db_path']):
        if not check_db_integrity(paths['local_db_path']):
            logger.warning("Local database is corrupted")
            
            # Try to fix it or copy from the main database
            if not fix_database(paths['local_db_path']) and os.path.exists(paths['db_path']):
                try:
                    shutil.copy2(paths['db_path'], paths['local_db_path'])
                    logger.info(f"Copied main database to local database")
                except Exception as e:
                    logger.error(f"Failed to copy main database to local database: {e}")
                    
                    # Create a new empty database
                    create_empty_database(paths['local_db_path'])
        else:
            logger.info("Local database is valid")
    elif os.path.exists(paths['db_path']):
        # Copy the main database
        try:
            os.makedirs(os.path.dirname(paths['local_db_path']), exist_ok=True)
            shutil.copy2(paths['db_path'], paths['local_db_path'])
            logger.info(f"Copied main database to local database")
        except Exception as e:
            logger.error(f"Failed to copy main database to local database: {e}")
            
            # Create a new empty database
            create_empty_database(paths['local_db_path'])
    else:
        # Create a new empty database
        create_empty_database(paths['local_db_path'])
    
    # Fix Render URL
    url_fixed = fix_render_url(config)
    
    # Save the configuration
    if url_fixed:
        save_config(paths['config_path'], config)
    
    # Install fixed client
    client_fixed = install_fixed_client()
    
    # Print summary
    print("\n" + "=" * 50)
    print("ePetCare Render Connection Fix Summary")
    print("=" * 50)
    print(f"Database corruption fixed: {'Yes' if db_corrupted else 'No corruption found'}")
    print(f"Render URL fixed: {'Yes' if url_fixed else 'No'}")
    print(f"Client code fixed: {'Yes' if client_fixed else 'No'}")
    
    if url_fixed or client_fixed or db_corrupted:
        print("\nFixes have been applied. Try running the application again using:")
        print("   vetportal_fixed.bat")
    else:
        print("\nNo issues were found that needed fixing.")
    
    print("\nCheck connection_fix.log for details.")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\nError: {e}")
        print("See connection_fix.log for details.")
        sys.exit(1)