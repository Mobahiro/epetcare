"""
ePetCare Database Sync Monitor

This script runs in the background and monitors the synchronization between
the local Vet Portal and the remote Render website. It can detect and fix
common synchronization issues automatically.

Usage: python monitor_db_sync.py [--fix]
"""

import os
import sys
import json
import time
import logging
import sqlite3
import requests
import tempfile
import argparse
import threading
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_sync_monitor.log')
    ]
)
logger = logging.getLogger('epetcare_monitor')

# Global variables
config = None
sync_status = {
    "last_check": None,
    "last_success": None,
    "errors": [],
    "status": "unknown",
    "is_running": False,
}
shutdown_event = threading.Event()

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
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

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

def test_api_connection(base_url, username=None, password=None):
    """Test connection to API endpoints"""
    results = []
    
    if base_url.endswith('/'):
        base_url = base_url.rstrip('/')
    
    # Test 1: Base URL connection
    try:
        response = requests.get(base_url, timeout=10)
        results.append({
            'endpoint': base_url,
            'status': response.status_code,
            'success': response.status_code < 400,
            'content_type': response.headers.get('content-type', '')
        })
    except Exception as e:
        results.append({
            'endpoint': base_url,
            'status': 'error',
            'success': False,
            'error': str(e)
        })
    
    # Test 2: Authentication
    if username and password:
        auth_endpoints = [
            f"{base_url}/api-token-auth/",
            f"{base_url}/api/token/",
            f"{base_url}/vet_portal/api-token-auth/",
        ]
        
        for endpoint in auth_endpoints:
            try:
                auth_response = requests.post(
                    endpoint,
                    data={'username': username, 'password': password},
                    timeout=10
                )
                
                auth_data = {}
                try:
                    if auth_response.status_code == 200:
                        auth_data = auth_response.json()
                except:
                    pass
                
                results.append({
                    'endpoint': endpoint,
                    'status': auth_response.status_code,
                    'success': auth_response.status_code == 200,
                    'token': bool(auth_data.get('token') or auth_data.get('access')),
                })
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'status': 'error',
                    'success': False,
                    'error': str(e)
                })
    
    # Test 3: API endpoints
    api_endpoints = [
        f"{base_url}/api/database/sync/",
        f"{base_url}/vet_portal/api/database/sync/",
        f"{base_url}/api/v1/database/sync/",
        f"{base_url}/database/sync/"
    ]
    
    for endpoint in api_endpoints:
        try:
            headers = {}
            if username and password:
                import base64
                auth_string = f"{username}:{password}"
                auth_bytes = auth_string.encode('utf-8')
                auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
                headers['Authorization'] = f"Basic {auth_b64}"
            
            api_response = requests.get(endpoint, headers=headers, timeout=10)
            
            api_data = {}
            try:
                if api_response.status_code == 200:
                    api_data = api_response.json()
            except:
                pass
            
            results.append({
                'endpoint': endpoint,
                'status': api_response.status_code,
                'success': api_response.status_code == 200,
                'data': bool(api_data),
                'data_keys': list(api_data.keys()) if api_data else []
            })
        except Exception as e:
            results.append({
                'endpoint': endpoint,
                'status': 'error',
                'success': False,
                'error': str(e)
            })
    
    return results

def sync_database():
    """Synchronize the local database with the remote database"""
    global config, sync_status
    
    if not config:
        config = load_config()
    
    # Check if sync is enabled
    if not config.get('remote_database', {}).get('enabled', True):
        logger.info("Remote database sync is disabled in config")
        sync_status["status"] = "disabled"
        return False
    
    # Get database paths
    db_path = config.get('database', {}).get('path')
    if not db_path:
        logger.error("No database path configured")
        sync_status["status"] = "error"
        sync_status["errors"].append("No database path configured")
        return False
    
    # Check local database
    db_ok, db_msg, db_conn = check_local_database(db_path)
    if not db_ok:
        logger.error(f"Local database error: {db_msg}")
        sync_status["status"] = "error"
        sync_status["errors"].append(f"Local database error: {db_msg}")
        return False
    
    if db_conn:
        db_conn.close()
    
    # Get remote database info
    remote_db = config.get('remote_database', {})
    url = remote_db.get('url')
    username = remote_db.get('username')
    password = remote_db.get('password')
    
    if not url:
        logger.error("No remote database URL configured")
        sync_status["status"] = "error"
        sync_status["errors"].append("No remote database URL configured")
        return False
    
    # Test API connection
    logger.info(f"Testing API connection to {url}")
    results = test_api_connection(url, username, password)
    
    # Check for successful endpoints
    successful = [r for r in results if r.get('success')]
    if not successful:
        logger.error("No API endpoints are accessible")
        sync_status["status"] = "error"
        sync_status["errors"].append("No API endpoints are accessible")
        return False
    
    # Find the best working sync endpoint
    sync_endpoints = [r for r in successful if 'sync' in r.get('endpoint', '')]
    if not sync_endpoints:
        logger.error("No sync endpoints available")
        sync_status["status"] = "error"
        sync_status["errors"].append("No sync endpoints available")
        return False
    
    sync_endpoint = sync_endpoints[0]['endpoint']
    logger.info(f"Using sync endpoint: {sync_endpoint}")
    
    # Find a token if available
    auth_results = [r for r in results if r.get('token')]
    auth_token = None
    if auth_results:
        auth_token = auth_results[0].get('token')
        logger.info("Using authentication token")
    
    # Try uploading the database
    upload_endpoint = sync_endpoint.replace('sync', 'upload')
    logger.info(f"Using upload endpoint: {upload_endpoint}")
    
    try:
        headers = {}
        if auth_token:
            headers['Authorization'] = f'Token {auth_token}'
        
        with open(db_path, 'rb') as f:
            logger.info("Uploading database...")
            response = requests.post(
                upload_endpoint,
                headers=headers,
                files={'database': f},
                timeout=60
            )
        
        if response.status_code == 200:
            logger.info("Database upload successful")
            sync_status["status"] = "success"
            sync_status["last_success"] = datetime.now()
            return True
        else:
            logger.error(f"Database upload failed: {response.status_code} - {response.text}")
            sync_status["status"] = "error"
            sync_status["errors"].append(f"Upload failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error uploading database: {e}")
        sync_status["status"] = "error"
        sync_status["errors"].append(f"Upload error: {str(e)}")
        return False

def monitor_thread(interval=60, auto_fix=False):
    """Background thread for monitoring database sync"""
    global sync_status
    
    logger.info(f"Monitor thread started with interval {interval} seconds")
    sync_status["is_running"] = True
    
    while not shutdown_event.is_set():
        try:
            logger.info("Checking database sync...")
            sync_status["last_check"] = datetime.now()
            
            # Clear previous errors
            sync_status["errors"] = []
            
            # Perform sync check
            sync_result = sync_database()
            
            # Log result
            if sync_result:
                logger.info("Sync successful")
            else:
                logger.warning("Sync failed")
                
                # Auto-fix if enabled
                if auto_fix:
                    logger.info("Attempting to fix sync issues...")
                    fix_sync_issues()
            
        except Exception as e:
            logger.error(f"Error in monitor thread: {e}")
            sync_status["status"] = "error"
            sync_status["errors"].append(f"Monitor error: {str(e)}")
        
        # Wait for the next interval or until shutdown
        shutdown_event.wait(interval)
    
    logger.info("Monitor thread stopped")
    sync_status["is_running"] = False

def fix_sync_issues():
    """Attempt to fix common sync issues"""
    global config
    
    try:
        # Fix 1: Check network connectivity
        try:
            requests.get("https://www.google.com", timeout=5)
        except:
            logger.error("Network connectivity issues detected")
            return False
        
        # Fix 2: Check and repair remote_db_client.py
        try:
            from diagnose_db_sync import fix_remote_db_client
            fixed = fix_remote_db_client()
            if fixed:
                logger.info("Fixed issues in remote_db_client.py")
        except ImportError:
            logger.warning("diagnose_db_sync.py not found, skipping client fix")
        
        # Fix 3: Check local database integrity and repair if needed
        db_path = config.get('database', {}).get('path')
        if db_path and os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.execute("PRAGMA integrity_check")
                conn.close()
            except sqlite3.DatabaseError:
                logger.error("Local database is corrupted, attempting repair")
                
                # Try to repair by reloading from a backup
                backup_dir = config.get('database', {}).get('backup_dir', 'backups')
                if os.path.isdir(backup_dir):
                    backups = [f for f in os.listdir(backup_dir) if f.endswith('.sqlite3')]
                    if backups:
                        # Use the most recent backup
                        latest_backup = sorted(backups)[-1]
                        backup_path = os.path.join(backup_dir, latest_backup)
                        
                        # Create a backup of the corrupted database
                        corrupt_backup = f"{db_path}.corrupted.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        import shutil
                        shutil.copy2(db_path, corrupt_backup)
                        
                        # Restore from backup
                        shutil.copy2(backup_path, db_path)
                        logger.info(f"Restored database from backup: {backup_path}")
        
        # Fix 4: Update config if needed
        if 'remote_database' in config:
            remote_db = config['remote_database']
            if 'url' in remote_db and remote_db['url'].endswith('/'):
                remote_db['url'] = remote_db['url'].rstrip('/')
                
            # Save updated config
            try:
                config_path = os.path.join('vet_desktop_app', 'config.json')
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                logger.info("Updated configuration file")
            except Exception as e:
                logger.error(f"Failed to update config: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing sync issues: {e}")
        return False

def main():
    global config
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='ePetCare Database Sync Monitor')
    parser.add_argument('--interval', type=int, default=60, help='Sync check interval in seconds (default: 60)')
    parser.add_argument('--fix', action='store_true', help='Automatically fix sync issues when detected')
    parser.add_argument('--background', action='store_true', help='Run in background mode')
    args = parser.parse_args()
    
    print_header("ePetCare Database Sync Monitor")
    
    # Load configuration
    config = load_config()
    if not config:
        print_status("Failed to load configuration", False)
        return
    
    # Override interval from config if available
    if 'remote_database' in config and 'sync_interval' in config['remote_database']:
        sync_interval = config['remote_database']['sync_interval']
        if args.interval == 60:  # Only if not explicitly set by user
            args.interval = sync_interval
    
    if args.background:
        # Run in background mode
        print_status(f"Starting monitor in background mode (interval: {args.interval}s)")
        monitor_thread_obj = threading.Thread(
            target=monitor_thread, 
            args=(args.interval, args.fix),
            daemon=True
        )
        monitor_thread_obj.start()
        
        # Wait for Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            shutdown_event.set()
            monitor_thread_obj.join(timeout=5)
            print("Monitor stopped")
    else:
        # Run once
        print_status("Running single sync check...")
        success = sync_database()
        
        if success:
            print_status("Database sync successful")
        else:
            print_status("Database sync failed", False)
            
            if args.fix:
                print_status("Attempting to fix sync issues...")
                fixed = fix_sync_issues()
                if fixed:
                    print_status("Sync issues fixed, retrying...")
                    success = sync_database()
                    if success:
                        print_status("Database sync successful after fixes")
                    else:
                        print_status("Database sync still failing after fixes", False)
                else:
                    print_status("Failed to fix sync issues", False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        shutdown_event.set()
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\nError: {e}")
        if shutdown_event:
            shutdown_event.set()