"""
Database Sync Diagnostics and Fix Tool for ePetCare

This script helps diagnose and fix synchronization issues between your local
vet portal application and the remote Render database.

Usage: python fix_db_sync.py
"""

import os
import sys
import json
import logging
import requests
import sqlite3
import shutil
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_sync_fix.log')
    ]
)
logger = logging.getLogger('epetcare_fix')

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_status(message, success=True):
    icon = "✓" if success else "✗"
    print(f" {icon} {message}")

def get_config():
    """Load the configuration from config.json"""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None

def update_config(config):
    """Update the config.json file"""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return False

def check_local_db(config):
    """Check if the local database exists and is valid"""
    db_path = config.get('database', {}).get('path')
    if not db_path:
        return False, "No database path configured"
    
    # Convert Windows path if needed
    db_path = os.path.normpath(db_path)
    
    if not os.path.exists(db_path):
        return False, f"Database file not found at {db_path}"
    
    # Check if it's a valid SQLite database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 'ok':
            return True, f"Local database is valid: {db_path}"
        else:
            return False, f"Database integrity check failed: {result[0] if result else 'unknown error'}"
    except Exception as e:
        return False, f"Error checking database: {e}"

def check_render_connection(config):
    """Check if the Render connection is working"""
    remote_db = config.get('remote_database', {})
    url = remote_db.get('url')
    username = remote_db.get('username')
    password = remote_db.get('password')
    
    if not url:
        return False, "No remote database URL configured"
    
    # Test base URL connection
    try:
        response = requests.get(url, timeout=10)
        if response.status_code >= 400:
            return False, f"Failed to connect to {url}: {response.status_code}"
        logger.info(f"Successfully connected to {url}")
    except Exception as e:
        return False, f"Error connecting to {url}: {e}"
    
    # Test authentication if credentials provided
    if username and password:
        auth_urls = [
            f"{url}/api-token-auth/",
            f"{url}/api/token/",
            f"{url}/vet_portal/api-token-auth/",
        ]
        
        for auth_url in auth_urls:
            try:
                auth_response = requests.post(
                    auth_url,
                    data={"username": username, "password": password},
                    timeout=10
                )
                
                if auth_response.status_code == 200:
                    return True, f"Authentication successful at {auth_url}"
            except:
                continue
    
    # Test API endpoints
    api_endpoints = [
        f"{url}/api/database/sync/",
        f"{url}/vet_portal/api/database/sync/",
        f"{url}/api/v1/database/sync/"
    ]
    
    for endpoint in api_endpoints:
        try:
            endpoint_response = requests.get(endpoint, timeout=10)
            if endpoint_response.status_code == 200:
                return True, f"API endpoint accessible: {endpoint}"
        except:
            continue
    
    return False, "Could not find working API endpoints"

def fix_config_issues(config):
    """Fix common configuration issues"""
    changes_made = False
    
    # Fix database path
    db_config = config.get('database', {})
    db_path = db_config.get('path')
    
    if db_path and '\\\\' in db_path:
        # Fix double backslashes in path
        db_config['path'] = db_path.replace('\\\\', '\\')
        config['database'] = db_config
        changes_made = True
    
    # Make sure database path exists
    if db_path:
        db_dir = os.path.dirname(os.path.normpath(db_path))
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                print_status(f"Created directory: {db_dir}")
            except Exception as e:
                logger.error(f"Failed to create directory {db_dir}: {e}")
    
    # Fix remote database URL
    remote_db = config.get('remote_database', {})
    url = remote_db.get('url')
    
    if url:
        # Remove trailing slashes
        if url.endswith('/'):
            remote_db['url'] = url.rstrip('/')
            changes_made = True
        
        # Make sure it has https://
        if not url.startswith('http'):
            remote_db['url'] = 'https://' + url
            changes_made = True
        
        # Make sure username and password are set
        if not remote_db.get('username') or not remote_db.get('password'):
            remote_db['username'] = 'admin'  # Default username
            remote_db['password'] = 'admin'  # Default password
            print_status("Set default username/password (admin/admin). Update with real credentials!", False)
            changes_made = True
        
        config['remote_database'] = remote_db
    
    return changes_made, config

def test_api_endpoints(base_url):
    """Test various API endpoints to find working ones"""
    if base_url.endswith('/'):
        base_url = base_url.rstrip('/')
    
    endpoints = [
        f"{base_url}/api/database/sync/",
        f"{base_url}/vet_portal/api/database/sync/",
        f"{base_url}/api/v1/database/sync/",
        f"{base_url}/database/sync/"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                print_status(f"Endpoint works: {endpoint}")
                working_endpoints.append(endpoint)
            else:
                print_status(f"Endpoint returned {response.status_code}: {endpoint}", False)
        except Exception as e:
            print_status(f"Endpoint error: {endpoint} - {e}", False)
    
    return working_endpoints

def create_test_db():
    """Create a test database file that can be used for testing uploads"""
    try:
        temp_path = os.path.join(tempfile.gettempdir(), 'epetcare_test.sqlite3')
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        
        # Create a simple test table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_sync (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            message TEXT
        )
        ''')
        
        # Insert a test row
        cursor.execute(
            "INSERT INTO test_sync (timestamp, message) VALUES (datetime('now'), ?)",
            [f"Sync test from {os.environ.get('COMPUTERNAME', 'local')} at {os.environ.get('USERNAME', 'user')}"]
        )
        
        conn.commit()
        conn.close()
        
        print_status(f"Created test database at {temp_path}")
        return temp_path
    except Exception as e:
        logger.error(f"Failed to create test database: {e}")
        return None

def test_upload(endpoint, test_db_path):
    """Test uploading to an endpoint"""
    try:
        print(f"Testing upload to {endpoint}...")
        
        with open(test_db_path, 'rb') as f:
            files = {'database': f}
            response = requests.post(endpoint, files=files, timeout=30)
        
        if response.status_code == 200:
            print_status(f"Upload successful to {endpoint}")
            return True
        else:
            print_status(f"Upload failed with status {response.status_code}: {response.text}", False)
            return False
    except Exception as e:
        print_status(f"Upload error: {e}", False)
        return False

def fix_remote_db_client():
    """Fix issues in the remote_db_client.py file"""
    try:
        client_path = os.path.join('vet_desktop_app', 'utils', 'remote_db_client.py')
        backup_path = client_path + '.bak'
        
        # Create a backup
        shutil.copy2(client_path, backup_path)
        print_status(f"Created backup of remote_db_client.py at {backup_path}")
        
        # Read the file content
        with open(client_path, 'r') as f:
            content = f.read()
        
        # Make fixes
        fixes_made = []
        
        # Fix 1: API URL construction
        if "if '/vet_portal/api' not in self.base_url:" in content:
            content = content.replace(
                "if '/vet_portal/api' not in self.base_url:",
                "# Check various API path patterns\n        api_paths = ['/api', '/vet_portal/api', '/api/v1']\n        path_found = False\n        for path in api_paths:\n            if path in self.base_url:\n                self.api_url = self.base_url\n                self.base_url = self.base_url.split(path)[0]\n                path_found = True\n                break\n        \n        if not path_found:"
            )
            fixes_made.append("API URL construction")
        
        # Fix 2: API endpoint discovery
        if "alt_paths = [" in content:
            content = content.replace(
                "alt_paths = [",
                "api_endpoints = [\n                    # Standard API patterns\n                    f\"{self.base_url}/api/database/sync/\",\n                    f\"{self.api_url}/database/sync/\",\n                    f\"{self.base_url}/vet_portal/api/database/sync/\",\n                    f\"{self.base_url}/api/v1/database/sync/\",\n                    # Direct database endpoints\n                    f\"{self.base_url}/database/sync/\",\n                    # Legacy endpoints"
            )
            fixes_made.append("API endpoint discovery")
        
        # Save the modified file
        with open(client_path, 'w') as f:
            f.write(content)
        
        if fixes_made:
            print_status(f"Fixed issues in remote_db_client.py: {', '.join(fixes_made)}")
            return True
        else:
            print_status("No fixes needed in remote_db_client.py")
            return False
    except Exception as e:
        logger.error(f"Failed to fix remote_db_client.py: {e}")
        return False

def main():
    print_header("ePetCare Database Sync Diagnostics and Fix Tool")
    
    # Step 1: Load configuration
    print("\nStep 1: Checking configuration...")
    config = get_config()
    if not config:
        print_status("Failed to load configuration", False)
        return
    
    # Step 2: Check local database
    print("\nStep 2: Checking local database...")
    db_ok, db_msg = check_local_db(config)
    print_status(db_msg, db_ok)
    
    if not db_ok:
        print("\nTrying to fix local database issues...")
        # Check if database directory exists
        db_path = config.get('database', {}).get('path')
        if db_path:
            db_dir = os.path.dirname(os.path.normpath(db_path))
            os.makedirs(db_dir, exist_ok=True)
            print_status(f"Created directory: {db_dir}")
    
    # Step 3: Check config for common issues
    print("\nStep 3: Checking for configuration issues...")
    changes_made, fixed_config = fix_config_issues(config)
    if changes_made:
        print_status("Fixed configuration issues")
        if update_config(fixed_config):
            print_status("Updated configuration file")
            config = fixed_config
        else:
            print_status("Failed to update configuration file", False)
    else:
        print_status("No configuration issues found")
    
    # Step 4: Check Render connection
    print("\nStep 4: Checking Render connection...")
    conn_ok, conn_msg = check_render_connection(config)
    print_status(conn_msg, conn_ok)
    
    # Step 5: Test API endpoints
    print("\nStep 5: Testing API endpoints...")
    base_url = config.get('remote_database', {}).get('url')
    if base_url:
        working_endpoints = test_api_endpoints(base_url)
        
        if working_endpoints:
            # Step 6: Test database uploads
            print("\nStep 6: Testing database uploads...")
            test_db = create_test_db()
            if test_db:
                upload_endpoints = [endpoint.replace('sync', 'upload') for endpoint in working_endpoints]
                
                for endpoint in upload_endpoints:
                    test_upload(endpoint, test_db)
            
            # Step 7: Fix remote_db_client.py
            print("\nStep 7: Fixing remote_db_client.py...")
            fix_remote_db_client()
    
    # Step 8: Summary and recommendations
    print_header("Summary and Recommendations")
    
    if not db_ok:
        print("\n➤ Local Database Issues:")
        print("  - Make sure your database exists at the configured path")
        print("  - Run Django migrations if the database is new or corrupted:")
        print("    python manage.py migrate")
    
    if not conn_ok:
        print("\n➤ Render Connection Issues:")
        print("  - Check if your Render app is deployed and running")
        print("  - Verify the URL in your configuration")
        print("  - Make sure your Render database is properly configured")
    
    print("\n➤ Next Steps:")
    print("  1. Restart your vet portal application")
    print("  2. Check the logs for any sync errors")
    print("  3. If errors persist, try manually syncing the database:")
    print("     - Use the migrate_to_render.py script for initial setup")
    print("     - Use the force_sync method in your application")
    
    print("\nDiagnostics complete! Check db_sync_fix.log for detailed information.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\nError: {e}")
        print("See db_sync_fix.log for details")