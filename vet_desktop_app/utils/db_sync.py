"""
Database synchronization utilities for the ePetCare Vet Desktop application.
This module provides functions to keep the database in sync with the main database.
"""

import os
import sys
import time
import sqlite3
import logging
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger('epetcare')

class DatabaseSyncManager(QObject):
    """
    Database synchronization manager for keeping the local database in sync with the main database.
    """
    
    sync_started = Signal()
    sync_completed = Signal(bool, str)  # Success, Message
    db_updated = Signal()  # Emitted when database is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sync_thread = None
        self.stop_event = threading.Event()
        self.sync_interval = 5  # Default to 5 seconds for real-time updates
        self.main_db_path = None
        self.local_db_path = None
        self.last_sync_time = 0
        self.is_syncing = False
    
    def setup(self, main_db_path, local_db_path=None, sync_interval=5):
        """
        Set up the database synchronization manager.
        
        Args:
            main_db_path: Path to the main database
            local_db_path: Path to the local database (optional)
            sync_interval: Sync interval in seconds
        """
        self.main_db_path = os.path.normpath(main_db_path)
        
        if local_db_path:
            self.local_db_path = os.path.normpath(local_db_path)
        else:
            # Use main database directly if no local database specified
            self.local_db_path = self.main_db_path
            
        self.sync_interval = sync_interval
        logger.info(f"Database sync manager set up with main DB: {self.main_db_path}, local DB: {self.local_db_path}")
        
        # If using a local copy, ensure it exists and is up to date
        if self.local_db_path != self.main_db_path:
            self._ensure_local_db()
    
    def _ensure_local_db(self):
        """Ensure the local database exists and is up to date"""
        if not os.path.exists(self.main_db_path):
            logger.error(f"Main database not found at {self.main_db_path}")
            return False
            
        # Create directory for local DB if it doesn't exist
        os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
        
        # If local DB doesn't exist or is empty, copy from main DB
        if not os.path.exists(self.local_db_path) or os.path.getsize(self.local_db_path) == 0:
            logger.info(f"Creating local database from main database")
            try:
                import shutil
                shutil.copy2(self.main_db_path, self.local_db_path)
                logger.info(f"Local database created successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to create local database: {e}")
                return False
        
        return True
    
    def start_sync(self):
        """Start the database synchronization thread"""
        if self.sync_thread and self.sync_thread.is_alive():
            logger.warning("Sync thread already running")
            return False
            
        if not self.main_db_path or not os.path.exists(self.main_db_path):
            logger.error(f"Main database not found at {self.main_db_path}")
            return False
            
        self.stop_event.clear()
        self.sync_thread = threading.Thread(target=self._sync_loop)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        logger.info("Database sync thread started")
        return True
    
    def stop_sync(self):
        """Stop the database synchronization thread"""
        if self.sync_thread and self.sync_thread.is_alive():
            self.stop_event.set()
            self.sync_thread.join(timeout=5)
            logger.info("Database sync thread stopped")
            return True
        return False
    
    def _sync_loop(self):
        """Main synchronization loop"""
        while not self.stop_event.is_set():
            try:
                # If using the main database directly, just check for changes
                if self.local_db_path == self.main_db_path:
                    self._check_for_changes()
                else:
                    # Otherwise, synchronize the local database with the main database
                    self._sync_databases()
                    
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
            # Wait for the next sync interval
            self.stop_event.wait(self.sync_interval)
    
    def _check_for_changes(self):
        """Check if the main database has changed"""
        try:
            # Check if the file exists before checking its modification time
            if not os.path.exists(self.main_db_path):
                logger.warning(f"Database file not found at {self.main_db_path}")
                return
                
            current_mtime = os.path.getmtime(self.main_db_path)
            if current_mtime > self.last_sync_time:
                logger.debug(f"Database file changed (mtime: {current_mtime}, last sync: {self.last_sync_time})")
                self.last_sync_time = current_mtime
                self.db_updated.emit()
        except Exception as e:
            logger.error(f"Error checking for database changes: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _sync_databases(self):
        """Synchronize the local database with the main database"""
        if self.is_syncing:
            return
            
        self.is_syncing = True
        self.sync_started.emit()
        
        try:
            # Check if the main database exists
            if not os.path.exists(self.main_db_path):
                logger.warning(f"Main database not found at {self.main_db_path}")
                self.sync_completed.emit(False, f"Main database not found at {self.main_db_path}")
                self.is_syncing = False
                return
                
            # Check if the main database is empty
            if os.path.getsize(self.main_db_path) == 0:
                logger.warning(f"Main database is empty at {self.main_db_path}")
                self.sync_completed.emit(False, f"Main database is empty at {self.main_db_path}")
                self.is_syncing = False
                return
                
            main_mtime = os.path.getmtime(self.main_db_path)
            
            # If main DB hasn't changed since last sync, no need to sync
            if main_mtime <= self.last_sync_time:
                self.is_syncing = False
                return
                
            logger.info(f"Syncing database from {self.main_db_path} to {self.local_db_path}")
            
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
            
            # Copy the main database to the local database
            import shutil
            shutil.copy2(self.main_db_path, self.local_db_path)
            
            self.last_sync_time = main_mtime
            self.sync_completed.emit(True, "Database synchronized successfully")
            self.db_updated.emit()
            
        except Exception as e:
            logger.error(f"Error syncing databases: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.sync_completed.emit(False, str(e))
        finally:
            self.is_syncing = False
    
    def force_sync(self):
        """Force a database synchronization"""
        if self.local_db_path == self.main_db_path:
            # If using the main database directly, just emit the update signal
            self.db_updated.emit()
            return True
        else:
            # Otherwise, synchronize the local database with the main database
            return self._sync_databases()
