"""
ePetCare Database Sync Diagnostic Tool

This script performs a comprehensive test of the database synchronization
between the local Vet Portal and the remote Render website.
"""

import os
import sys
import json
import requests
import logging
import sqlite3
import tempfile
import shutil
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_sync_diagnostic.log')
    ]
)
logger = logging.getLogger('epetcare_diagnostic')

def print_header(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_status(message, success=True):
    """Print a status message with an icon"""
    icon = "✓" if success else "✗"
    print(f" {icon} {message}")

def load_config():
    """Load the configuration from config.json"""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def update_config(config):
    """Update the configuration in config.json"""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return False

def check_local_database(db_path):
    """
    Check if the local database is valid and can be opened.
    Returns (success, message, db_connection)
    """
    if not os.path.exists(db_path):
        return False, f"Database file not found at {db_path}", None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check database integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        if result != "ok":
            conn.close()
            return False, f"Database integrity check failed: {result}", None
        
        # Check for required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['auth_user', 'clinic_owner', 'clinic_pet', 'clinic_appointment']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            conn.close()
            return False, f"Database is missing required tables: {', '.join(missing_tables)}", None
        
        return True, "Local database is valid", conn
    except sqlite3.Error as e:
        return False, f"SQLite error: {e}", None
    except Exception as e:
        return False, f"Error checking database: {e}", None

def test_render_api(url, username=None, password=None, auth_token=None):
    """
    Test connectivity to the Render API.
    Returns (success, message, api_info)
    """
    api_info = {
        "base_url": url.rstrip('/'),
        "username": username,
        "password": password,
        "auth_token": auth_token,
        "working_endpoints": [],
        "auth_endpoint": None,
        "sync_endpoint": None,
        "download_endpoint": None,
        "upload_endpoint": None
    }
    
    # Parse the URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False, f"Invalid URL: {url}", api_info
    
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    api_info["base_url"] = base_url
    
    # Test base URL connection
    try:
        logger.info(f"Testing connection to {base_url}")
        response = requests.get(base_url, timeout=10)
        if response.status_code >= 400:
            return False, f"Failed to connect to {base_url}: {response.status_code}", api_info
    except Exception as e:
        return False, f"Error connecting to {base_url}: {e}", api_info
    
    # Test authentication if credentials provided
    if username and password:
        auth_endpoints = [
            f"{base_url}/api-token-auth/",
            f"{base_url}/api/token/",
            f"{base_url}/vet_portal/api-token-auth/",
            f"{base_url}/api/auth/"
        ]
        
        for auth_url in auth_endpoints:
            try:
                logger.info(f"Testing authentication at {auth_url}")
                auth_response = requests.post(
                    auth_url,
                    data={"username": username, "password": password},
                    timeout=10
                )
                
                if auth_response.status_code == 200:
                    try:
                        data = auth_response.json()
                        token = data.get('token') or data.get('access')
                        
                        if token:
                            api_info["auth_endpoint"] = auth_url
                            api_info["auth_token"] = token
                            api_info["working_endpoints"].append(auth_url)
                            logger.info(f"Authentication successful at {auth_url}")
                            break
                    except:
                        pass
            except:
                pass
    
    # Test API endpoints
    api_paths = [
        '/api',
        '/vet_portal/api',
        '/api/v1'
    ]
    
    sync_endpoints = []
    download_endpoints = []
    upload_endpoints = []
    
    for api_path in api_paths:
        # Test database sync endpoints
        sync_url = f"{base_url}{api_path}/database/sync/"
        try:
            logger.info(f"Testing sync endpoint {sync_url}")
            headers = {}
            if api_info["auth_token"]:
                headers['Authorization'] = f'Token {api_info["auth_token"]}'
            
            sync_response = requests.get(sync_url, headers=headers, timeout=10)
            if sync_response.status_code == 200:
                sync_endpoints.append(sync_url)
                api_info["working_endpoints"].append(sync_url)
                logger.info(f"Sync endpoint works: {sync_url}")
        except:
            pass
        
        # Test database download endpoints
        download_url = f"{base_url}{api_path}/database/download/"
        try:
            logger.info(f"Testing download endpoint {download_url}")
            headers = {}
            if api_info["auth_token"]:
                headers['Authorization'] = f'Token {api_info["auth_token"]}'
            
            download_response = requests.head(download_url, headers=headers, timeout=10)
            if download_response.status_code == 200:
                download_endpoints.append(download_url)
                api_info["working_endpoints"].append(download_url)
                logger.info(f"Download endpoint works: {download_url}")
        except:
            pass
        
        # Test database upload endpoints
        upload_url = f"{base_url}{api_path}/database/upload/"
        try:
            logger.info(f"Testing upload endpoint {upload_url}")
            headers = {}
            if api_info["auth_token"]:
                headers['Authorization'] = f'Token {api_info["auth_token"]}'
            
            # We'll just check if the endpoint exists without actually uploading
            upload_response = requests.options(upload_url, headers=headers, timeout=10)
            if upload_response.status_code < 405:  # Any response except 405 Method Not Allowed
                upload_endpoints.append(upload_url)
                api_info["working_endpoints"].append(upload_url)
                logger.info(f"Upload endpoint works: {upload_url}")
        except:
            pass
    
    # Set the best endpoints in the API info
    if sync_endpoints:
        api_info["sync_endpoint"] = sync_endpoints[0]
    if download_endpoints:
        api_info["download_endpoint"] = download_endpoints[0]
    if upload_endpoints:
        api_info["upload_endpoint"] = upload_endpoints[0]
    
    # Check if we have working endpoints
    if api_info["working_endpoints"]:
        return True, f"Successfully connected to {len(api_info['working_endpoints'])} API endpoints", api_info
    else:
        return False, "No working API endpoints found", api_info

def fix_remote_db_client():
    """Fix issues in the remote_db_client.py file"""
    try:
        client_path = os.path.join('vet_desktop_app', 'utils', 'remote_db_client.py')
        backup_path = client_path + '.bak'
        
        # Create a backup if it doesn't exist
        if not os.path.exists(backup_path):
            shutil.copy2(client_path, backup_path)
            print_status(f"Created backup of remote_db_client.py at {backup_path}")
        
        # Read the file content
        with open(client_path, 'r') as f:
            content = f.read()
        
        # Check for common issues
        issues_fixed = []
        
        # Fix indentation error around line 228
        if "def get_database_info(self):" in content:
            # Extract the get_database_info method
            start_marker = "def get_database_info(self):"
            start_idx = content.find(start_marker)
            
            # Find the next method definition to determine where this method ends
            next_def = content.find("def ", start_idx + len(start_marker))
            if next_def > 0:
                method_content = content[start_idx:next_def]
            else:
                # If no next method, look for class end
                class_end = content.find("class ", start_idx + len(start_marker))
                if class_end > 0:
                    method_content = content[start_idx:class_end]
                else:
                    # If can't find next class, take rest of file
                    method_content = content[start_idx:]
            
            # Check if method has indentation issues (duplicated code blocks)
            if method_content.count("return response.json()") > 1:
                # Replace the entire method with a fixed version
                fixed_method = """    def get_database_info(self):
        \"\"\"Get basic information about the remote database\"\"\"
        url = f"{self.base_url}/api/database-info/"
        try:
            response = requests.get(
                url, 
                headers=self.get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get database info: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error connecting to remote database: {str(e)}")
            return None
"""
                # Replace the method in the content
                if next_def > 0:
                    new_content = content[:start_idx] + fixed_method + content[next_def:]
                else:
                    new_content = content[:start_idx] + fixed_method
                
                content = new_content
                issues_fixed.append("indentation error in get_database_info method (line ~228)")
        
        # Fix issues with URL handling
        api_paths_check = "api_paths = [" in content and "'/api'," in content
        
        if not api_paths_check:
            # Add proper API paths handling
            content = content.replace(
                "        # Ensure we have the correct API endpoint",
                """        # Ensure we have the correct API endpoint
        # First, try to determine the correct API path based on common patterns
        api_paths = [
            '/api',                # Standard API path
            '/vet_portal/api',     # Legacy path
            '/api/v1',             # Versioned API
        ]
        
        # Set default API URL
        self.api_url = f"{self.base_url}/api"
        
        # Check if any API path is already in the URL
        path_found = False
        for path in api_paths:
            if path in self.base_url:
                self.api_url = self.base_url
                self.base_url = self.base_url.split(path)[0]
                path_found = True
                break"""
            )
            issues_fixed.append("API URL parsing")
        
        # Fix issues with API endpoint discovery
        if "api_endpoints = [" not in content:
            content = content.replace(
                "            alt_paths = [",
                """            api_endpoints = [
                # Standard API patterns
                f"{self.base_url}/api/database/sync/",
                f"{self.api_url}/database/sync/",
                f"{self.base_url}/vet_portal/api/database/sync/",
                f"{self.base_url}/api/v1/database/sync/",
                # Direct database endpoints
                f"{self.base_url}/database/sync/",
                # Legacy endpoints"""
            )
            issues_fixed.append("API endpoint discovery")
        
        # Fix duplicated code blocks in get_database_info
        if "                for alt_path in alt_paths:" in content and "alt_paths = [" not in content:
            # Remove duplicated block
            start_idx = content.find("                for alt_path in alt_paths:")
            end_idx = content.find("                # If we get here, all attempts failed", start_idx)
            if start_idx > 0 and end_idx > start_idx:
                content = content[:start_idx] + content[end_idx:]
                issues_fixed.append("duplicated code blocks")
        
        # Save the modified file if changes were made
        if issues_fixed:
            with open(client_path, 'w') as f:
                f.write(content)
            print_status(f"Fixed issues in remote_db_client.py: {', '.join(issues_fixed)}")
            return True
        else:
            print_status("No issues found in remote_db_client.py")
            return False
    except Exception as e:
        logger.error(f"Failed to fix remote_db_client.py: {e}")
        print_status(f"Error fixing remote_db_client.py: {e}", success=False)
        return False

def test_db_sync(config, api_info):
    """Test database synchronization"""
    # Create a small test database file
    temp_db_path = os.path.join(tempfile.gettempdir(), 'epetcare_test.sqlite3')
    try:
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_test (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            message TEXT
        )
        ''')
        
        # Add a test record
        cursor.execute(
            "INSERT INTO sync_test (timestamp, message) VALUES (?, ?)",
            (datetime.now().isoformat(), f"Test sync from {os.environ.get('COMPUTERNAME', 'unknown')} at {datetime.now().isoformat()}")
        )
        
        conn.commit()
        conn.close()
        
        print_status(f"Created test database at {temp_db_path}")
        
        # Test uploading the database
        if api_info["upload_endpoint"]:
            try:
                print_status(f"Testing upload to {api_info['upload_endpoint']}")
                
                headers = {}
                if api_info["auth_token"]:
                    headers['Authorization'] = f'Token {api_info["auth_token"]}'
                
                with open(temp_db_path, 'rb') as f:
                    files = {'database': f}
                    response = requests.post(
                        api_info["upload_endpoint"],
                        headers=headers,
                        files=files,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    print_status("Database upload successful")
                    return True
                else:
                    print_status(f"Database upload failed: {response.status_code} - {response.text}", False)
                    return False
            except Exception as e:
                print_status(f"Error uploading database: {e}", False)
                return False
        else:
            print_status("No upload endpoint available", False)
            return False
    except Exception as e:
        print_status(f"Error creating test database: {e}", False)
        return False
    finally:
        # Clean up
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except:
                pass

def fix_config(config, api_info):
    """Fix common configuration issues"""
    changes_made = False
    
    # Fix remote database URL
    remote_db = config.get('remote_database', {})
    url = remote_db.get('url')
    
    if url:
        # Update URL based on API test results
        if api_info["base_url"] and api_info["base_url"] != url:
            remote_db['url'] = api_info["base_url"]
            print_status(f"Updated remote database URL to {api_info['base_url']}")
            changes_made = True
        
        # Make sure username and password are set
        if api_info["username"] and not remote_db.get('username'):
            remote_db['username'] = api_info["username"]
            changes_made = True
            
        if api_info["password"] and not remote_db.get('password'):
            remote_db['password'] = api_info["password"]
            changes_made = True
            
        config['remote_database'] = remote_db
    
    return changes_made, config

def main():
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='ePetCare Database Sync Diagnostic Tool')
    parser.add_argument('--quick-fix', action='store_true', help='Apply quick fixes without full diagnostics')
    args = parser.parse_args()
    
    if args.quick_fix:
        # Apply quick fixes only
        fix_remote_db_client()
        return
    
    print_header("ePetCare Database Sync Diagnostic Tool")
    
    # Step 1: Load configuration
    print("\nStep 1: Loading configuration...")
    config = load_config()
    if not config:
        print_status("Failed to load configuration", False)
        return
    
    # Step 2: Check local database
    print("\nStep 2: Checking local database...")
    db_path = config.get('database', {}).get('path')
    if not db_path:
        print_status("No database path configured", False)
        return
    
    db_ok, db_msg, db_conn = check_local_database(db_path)
    print_status(db_msg, db_ok)
    
    if db_conn:
        db_conn.close()
    
    # Step 3: Check Render API connection
    print("\nStep 3: Checking Render API connection...")
    remote_db = config.get('remote_database', {})
    url = remote_db.get('url')
    username = remote_db.get('username')
    password = remote_db.get('password')
    
    if not url:
        print_status("No remote database URL configured", False)
        return
    
    api_ok, api_msg, api_info = test_render_api(url, username, password)
    print_status(api_msg, api_ok)
    
    if not api_ok:
        print_status("Failed to connect to Render API. Please check your URL and credentials.", False)
        return
    
    # Print detected API endpoints
    print("\nDetected API endpoints:")
    for endpoint in api_info["working_endpoints"]:
        print_status(f"Found: {endpoint}")
    
    # Step 4: Fix common issues
    print("\nStep 4: Fixing common issues...")
    
    # Fix remote_db_client.py
    fixed_client = fix_remote_db_client()
    
    # Fix config.json
    config_changed, fixed_config = fix_config(config, api_info)
    if config_changed:
        update_config(fixed_config)
        print_status("Updated config.json with fixed settings")
    else:
        print_status("No config.json changes needed")
    
    # Step 5: Test database synchronization
    print("\nStep 5: Testing database synchronization...")
    if api_info["upload_endpoint"] and api_info["sync_endpoint"]:
        test_db_sync(config, api_info)
    else:
        print_status("Skipping sync test as no upload/sync endpoints were found", False)
    
    # Step 6: Summary
    print_header("Summary")
    
    if api_ok:
        print_status("Render API connection successful")
        print_status(f"Authentication endpoint: {api_info['auth_endpoint'] or 'Not found'}")
        print_status(f"Sync endpoint: {api_info['sync_endpoint'] or 'Not found'}")
        print_status(f"Download endpoint: {api_info['download_endpoint'] or 'Not found'}")
        print_status(f"Upload endpoint: {api_info['upload_endpoint'] or 'Not found'}")
        
    # Recommendations
    print_header("Recommendations")
    
    if not db_ok:
        print("\n1. Local database issues:")
        print("   - Check if your local database exists and is not corrupted")
        print("   - Try running Django migrations: python manage.py migrate")
        print("   - If the database is completely corrupted, restore from a backup")
    
    if not api_ok:
        print("\n2. Render API connection issues:")
        print("   - Verify your Render URL is correct")
        print("   - Make sure your Render app is deployed and running")
        print("   - Check your username and password credentials")
    
    if not api_info["auth_endpoint"]:
        print("\n3. Authentication issues:")
        print("   - No working authentication endpoint found")
        print("   - Make sure your credentials are correct")
        print("   - Check if your Render app has authentication endpoints enabled")
    
    if not api_info["sync_endpoint"] or not api_info["download_endpoint"] or not api_info["upload_endpoint"]:
        print("\n4. Missing API endpoints:")
        if not api_info["sync_endpoint"]:
            print("   - No database sync endpoint found")
        if not api_info["download_endpoint"]:
            print("   - No database download endpoint found")
        if not api_info["upload_endpoint"]:
            print("   - No database upload endpoint found")
        print("   - Make sure your Render app has the database API endpoints enabled")
        print("   - Check if your Django app's URLs are properly configured")
    
    if fixed_client:
        print("\n5. Client code has been fixed:")
        print("   - Fixed issues in remote_db_client.py")
        print("   - Backup of the original file was created")
    
    if config_changed:
        print("\n6. Configuration has been updated:")
        print("   - Fixed issues in config.json")
        print("   - Remote database URL and credentials have been updated")
    
    print("\nNext steps:")
    print("1. Restart your vet portal application")
    print("2. Try to sync your database manually")
    print("3. Check the application logs for any remaining errors")
    print("4. If issues persist, check your Render application logs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\nError: {e}")