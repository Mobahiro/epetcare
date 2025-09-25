"""
Remote database client for connecting to ePetCare deployed on Render.
This module handles synchronization with the remote PostgreSQL database
through the API endpoints.
"""

import os
import json
import logging
import requests
import tempfile
from urllib.parse import urlparse

logger = logging.getLogger('epetcare')


class RemoteDatabaseClient:
    """
    Client for connecting to remote database via API.
    """
    
    def __init__(self):
        self.base_url = None
        self.api_token = None
        self.session = None
        self.authenticated = False
    
    def setup(self, base_url, username=None, password=None, token=None):
        """
        Set up the remote database client.
        
        Args:
            base_url: Base URL of the ePetCare API
            username: Username for authentication (optional if token is provided)
            password: Password for authentication (optional if token is provided)
            token: API token for authentication (optional if username/password are provided)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        logger.info(f"Setting up remote database client for {self.base_url}")
        
        if token:
            # Use token authentication if provided
            self.api_token = token
            self.session.headers.update({'Authorization': f'Token {token}'})
            self.authenticated = True
            logger.debug("Using token authentication")
            return True
        elif username and password:
            # Otherwise, try to authenticate with username and password
            return self._authenticate(username, password)
        else:
            logger.error("No authentication credentials provided")
            return False
    
    def _authenticate(self, username, password):
        """
        Authenticate with the API using username and password.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # Try to get a token from the API
            response = self.session.post(
                f"{self.base_url}/api-token-auth/",
                data={'username': username, 'password': password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.api_token = data.get('token')
                
                if self.api_token:
                    self.session.headers.update({'Authorization': f'Token {self.api_token}'})
                    self.authenticated = True
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.error("Authentication failed: No token in response")
                    return False
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def get_database_info(self):
        """
        Get information about the remote database.
        
        Returns:
            dict: Database information if successful, None otherwise
        """
        if not self.authenticated:
            logger.error("Not authenticated")
            return None
        
        try:
            response = self.session.get(f"{self.base_url}/vet_portal/api/database/sync/")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get database info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return None
    
    def download_database(self, local_path=None):
        """
        Download the database from the remote server.
        
        Args:
            local_path: Path where to save the database (optional)
            
        Returns:
            str: Path to the downloaded database if successful, None otherwise
        """
        if not self.authenticated:
            logger.error("Not authenticated")
            return None
        
        try:
            # Get database info first to check if direct download is supported
            db_info = self.get_database_info()
            
            if not db_info:
                logger.error("Failed to get database info")
                return None
            
            # Check if direct download is supported
            if db_info.get('sync_method') != 'file':
                logger.error("Direct database download not supported")
                return None
            
            # Download the database
            response = self.session.get(
                f"{self.base_url}/vet_portal/api/database/download/",
                stream=True
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to download database: {response.status_code} - {response.text}")
                return None
            
            # Save the database to a file
            if not local_path:
                temp_fd, local_path = tempfile.mkstemp(suffix='.sqlite3', prefix='epetcare_')
                os.close(temp_fd)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Database downloaded successfully to {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading database: {e}")
            return None
    
    def upload_database(self, local_path):
        """
        Upload the local database to the remote server.
        
        Args:
            local_path: Path to the local database file
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        if not self.authenticated:
            logger.error("Not authenticated")
            return False
        
        try:
            # Get database info first to check if direct upload is supported
            db_info = self.get_database_info()
            
            if not db_info:
                logger.error("Failed to get database info")
                return False
            
            # Check if direct upload is supported
            if db_info.get('sync_method') != 'file':
                logger.error("Direct database upload not supported")
                return False
            
            # Upload the database
            with open(local_path, 'rb') as f:
                response = self.session.post(
                    f"{self.base_url}/vet_portal/api/database/upload/",
                    files={'database': f}
                )
            
            if response.status_code == 200:
                logger.info("Database uploaded successfully")
                return True
            else:
                logger.error(f"Failed to upload database: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading database: {e}")
            return False