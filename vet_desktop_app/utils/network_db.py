"""
Network database utilities for the ePetCare Vet Desktop application.
This module provides functions to connect to a remote database over the network.
"""

import os
import sys
import socket
import sqlite3
import logging
import requests
import tempfile
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger('epetcare')

class NetworkDatabaseManager:
    """
    Network database manager for connecting to a remote database.
    """
    
    def __init__(self):
        self.remote_url = None
        self.local_temp_path = None
        self.auth_token = None
        self.last_sync_time = 0
    
    def setup(self, remote_url, auth_token=None):
        """
        Set up the network database manager.
        
        Args:
            remote_url: URL to the remote database API
            auth_token: Authentication token for the API (optional)
        """
        self.remote_url = remote_url
        self.auth_token = auth_token
        
        # Create a temporary file for the local database
        temp_fd, self.local_temp_path = tempfile.mkstemp(suffix='.sqlite3', prefix='epetcare_')
        os.close(temp_fd)
        
        logger.info(f"Network database manager set up with remote URL: {self.remote_url}")
        logger.debug(f"Local temporary database path: {self.local_temp_path}")
        
        # Sync the database immediately
        return self.sync_database()
    
    def sync_database(self):
        """Synchronize the local database with the remote database"""
        if not self.remote_url:
            logger.error("Remote URL not set")
            return False
            
        try:
            logger.info(f"Syncing database from {self.remote_url}")
            
            # Prepare headers
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            # Download the database file
            response = requests.get(f"{self.remote_url}/download", headers=headers, stream=True)
            
            if response.status_code == 200:
                with open(self.local_temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Database downloaded successfully to {self.local_temp_path}")
                return True
            else:
                logger.error(f"Failed to download database: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error syncing database: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def upload_changes(self):
        """Upload local changes to the remote database"""
        if not self.remote_url or not self.local_temp_path:
            logger.error("Remote URL or local path not set")
            return False
            
        try:
            logger.info(f"Uploading changes to {self.remote_url}")
            
            # Prepare headers
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            # Upload the database file
            with open(self.local_temp_path, 'rb') as f:
                response = requests.post(
                    f"{self.remote_url}/upload",
                    headers=headers,
                    files={'database': f}
                )
            
            if response.status_code == 200:
                logger.info("Changes uploaded successfully")
                return True
            else:
                logger.error(f"Failed to upload changes: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading changes: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_local_path(self):
        """Get the path to the local temporary database"""
        return self.local_temp_path
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.local_temp_path and os.path.exists(self.local_temp_path):
            try:
                os.remove(self.local_temp_path)
                logger.debug(f"Removed temporary database file: {self.local_temp_path}")
            except Exception as e:
                logger.error(f"Error removing temporary database file: {e}")


def is_url(path):
    """Check if a path is a URL"""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_network_path(path):
    """Check if a path is a network path"""
    # Windows UNC path
    if path.startswith('\\\\'):
        return True
    
    # Check if it's a URL
    if is_url(path):
        return True
    
    return False


def is_remote_available(host, port=80, timeout=2):
    """Check if a remote host is available"""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, socket.error):
        return False
