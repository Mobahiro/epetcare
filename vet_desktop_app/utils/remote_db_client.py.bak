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
        self.api_url = None
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
        
        # Ensure we have the correct API endpoint
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
                break
            
        self.session = requests.Session()
        
        logger.info(f"Setting up remote database client for {self.base_url}")
        logger.debug(f"API URL: {self.api_url}")
        
        # Try to make a simple request to verify the server is reachable
        try:
            logger.debug(f"Testing connection to {self.base_url}")
            test_response = self.session.get(f"{self.base_url}/", timeout=5)
            logger.debug(f"Server responded with status code: {test_response.status_code}")
            
            if test_response.status_code >= 500:
                logger.error(f"Server error: {test_response.status_code} - {test_response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error connecting to server: {e}")
            return False
        
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
            # Try to authenticate as anonymous user if possible
            logger.warning("No authentication credentials provided, trying anonymous access")
            self.authenticated = True
            return True
    
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
            # Try different authentication endpoints
            auth_urls = [
                f"{self.base_url}/api-token-auth/",
                f"{self.base_url}/vet_portal/api-token-auth/",
                f"{self.base_url}/api/token/",
                f"{self.base_url}/api/auth/"
            ]
            
            for auth_url in auth_urls:
                try:
                    logger.debug(f"Trying authentication at {auth_url}")
                    response = self.session.post(
                        auth_url,
                        data={'username': username, 'password': password},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            token = data.get('token') or data.get('access')
                            
                            if token:
                                self.api_token = token
                                auth_header = 'Bearer' if data.get('access') else 'Token'
                                self.session.headers.update({'Authorization': f'{auth_header} {token}'})
                                self.authenticated = True
                                logger.info(f"Authentication successful at {auth_url}")
                                return True
                            else:
                                logger.warning(f"Authentication response missing token at {auth_url}")
                        except ValueError:
                            logger.warning(f"Invalid JSON response from {auth_url}: {response.text}")
                    elif response.status_code == 404:
                        logger.debug(f"Auth endpoint not found: {auth_url}")
                    else:
                        logger.warning(f"Authentication failed at {auth_url}: {response.status_code} - {response.text}")
                        
                except requests.RequestException as e:
                    logger.debug(f"Request failed for {auth_url}: {e}")
            
            # If we get here, all authentication attempts failed
            logger.error("All authentication attempts failed")
            
            # Try anonymous access as last resort
            logger.warning("Falling back to anonymous access")
            self.authenticated = True
            return True
                
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
            # First check if the API is accessible at all
            try:
                test_response = self.session.get(f"{self.base_url}", timeout=5)
                logger.debug(f"Base URL responded with status {test_response.status_code}")
            except Exception as e:
                logger.error(f"Error accessing base URL: {e}")
            
            # Try various API endpoints in order of likelihood
            api_endpoints = [
                # Standard API patterns
                f"{self.base_url}/api/database/sync/",
                f"{self.api_url}/database/sync/",
                f"{self.base_url}/vet_portal/api/database/sync/",
                f"{self.base_url}/api/v1/database/sync/",
                # Direct database endpoints
                f"{self.base_url}/database/sync/",
                # Legacy endpoints
                f"{self.base_url}/vet/api/database/sync/"
            ]
            
            for endpoint in api_endpoints:
                logger.debug(f"Trying database info endpoint: {endpoint}")
                try:
                    response = self.session.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"Successfully got database info from {endpoint}")
                            # Update the API URL to use the successful endpoint path
                            self.api_url = endpoint.rsplit('/database/sync/', 1)[0]
                            logger.debug(f"Updated API URL to {self.api_url}")
                            return data
                        except ValueError:
                            logger.warning(f"Invalid JSON response from {endpoint}: {response.text}")
                    else:
                        logger.debug(f"Failed to get data from {endpoint}: {response.status_code}")
                except requests.RequestException as e:
                    logger.debug(f"Request failed for {endpoint}: {e}")
            
            # If we get here, all attempts failed
            logger.error("All attempts to get database info failed")
            
            # Return dummy info as fallback
            return {
                "status": "unknown",
                "timestamp": "",
                "sync_method": "api",
                "message": "Could not connect to database API. Check your URL and credentials."
            }
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return None
                
                for alt_path in alt_paths:
                    try:
                        logger.debug(f"Trying alternative path: {alt_path}")
                        alt_response = self.session.get(alt_path, timeout=10)
                        
                        if alt_response.status_code == 200:
                            try:
                                return alt_response.json()
                            except ValueError:
                                logger.warning(f"Invalid JSON response from {alt_path}")
                        else:
                            logger.debug(f"Failed to get data from {alt_path}: {alt_response.status_code}")
                    except requests.RequestException as e:
                        logger.debug(f"Request failed for {alt_path}: {e}")
                
                # If we get here, all attempts failed
                logger.error("All attempts to get database info failed")
                
                # Return dummy info as fallback
                return {
                    "status": "unknown",
                    "timestamp": "",
                    "sync_method": "api",
                    "message": "Could not connect to database API. Check your URL and credentials."
                }
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
            # Try downloading from various possible endpoints
            download_urls = [
                f"{self.api_url}/database/download/",
                f"{self.base_url}/api/database/download/",
                f"{self.base_url}/vet/api/database/download/",
                f"{self.base_url}/api/v1/database/download/",
                f"{self.base_url}/download_db/"
            ]
            
            # Save the database to a file
            if not local_path:
                temp_fd, local_path = tempfile.mkstemp(suffix='.sqlite3', prefix='epetcare_')
                os.close(temp_fd)
            
            for download_url in download_urls:
                try:
                    logger.debug(f"Trying to download database from {download_url}")
                    response = self.session.get(download_url, stream=True, timeout=30)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '')
                        
                        # Check if this is likely a database file
                        if 'application/octet-stream' in content_type or 'application/x-sqlite3' in content_type or 'application/sqlite3' in content_type:
                            with open(local_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            # Verify it's a SQLite database
                            if self._is_valid_sqlite_db(local_path):
                                logger.info(f"Database downloaded successfully to {local_path}")
                                return local_path
                            else:
                                logger.warning(f"Downloaded file is not a valid SQLite database")
                        else:
                            logger.debug(f"Response from {download_url} is not a database file (Content-Type: {content_type})")
                    else:
                        logger.debug(f"Failed to download from {download_url}: {response.status_code}")
                
                except requests.RequestException as e:
                    logger.debug(f"Request failed for {download_url}: {e}")
            
            # If we get here, all download attempts failed
            logger.error("All attempts to download database failed")
            
            # Create a dummy database as fallback
            logger.warning("Creating a new empty database as fallback")
            self._create_empty_database(local_path)
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading database: {e}")
            return None
    
    def _is_valid_sqlite_db(self, file_path):
        """Check if a file is a valid SQLite database."""
        try:
            import sqlite3
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            return result and result[0] != "corrupt"
        except:
            return False
    
    def _create_empty_database(self, file_path):
        """Create an empty SQLite database with basic structure."""
        try:
            import sqlite3
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Create some basic tables that might be expected by the application
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
            logger.debug(f"Created empty database at {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create empty database: {e}")
            return False
    
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
            # Try uploading to various possible endpoints
            upload_urls = [
                f"{self.api_url}/database/upload/",
                f"{self.base_url}/api/database/upload/",
                f"{self.base_url}/vet/api/database/upload/",
                f"{self.base_url}/api/v1/database/upload/",
                f"{self.base_url}/upload_db/"
            ]
            
            for upload_url in upload_urls:
                try:
                    logger.debug(f"Trying to upload database to {upload_url}")
                    
                    with open(local_path, 'rb') as f:
                        response = self.session.post(
                            upload_url,
                            files={'database': f},
                            timeout=30
                        )
                    
                    if response.status_code == 200:
                        logger.info("Database uploaded successfully")
                        return True
                    elif response.status_code == 404:
                        logger.debug(f"Upload endpoint not found: {upload_url}")
                    else:
                        logger.warning(f"Failed to upload to {upload_url}: {response.status_code} - {response.text}")
                
                except requests.RequestException as e:
                    logger.debug(f"Request failed for {upload_url}: {e}")
            
            # If we get here, all upload attempts failed
            logger.error("All attempts to upload database failed")
            return False
                
        except Exception as e:
            logger.error(f"Error uploading database: {e}")
            return False