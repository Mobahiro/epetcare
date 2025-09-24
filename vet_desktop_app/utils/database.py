"""
Database utility functions for the ePetCare Vet Desktop Application.
"""

import os
import sqlite3
import logging
import time
import shutil
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union

logger = logging.getLogger('epetcare')

# Global database connection
db_connection = None

# Import QMessageBox for error dialogs
try:
    from PySide6.QtWidgets import QMessageBox
except ImportError:
    # Fallback for when PySide6 is not available (e.g., during initial setup)
    class QMessageBox:
        @staticmethod
        def critical(parent, title, message):
            logger.critical(f"{title}: {message}")
            print(f"\n{title}: {message}")

def get_connection():
    """
    Get the current database connection.
    
    Returns:
        sqlite3.Connection: The current database connection
    """
    global db_connection
    if db_connection is None:
        raise ValueError("Database connection not initialized. Call setup_database_connection first.")
    return db_connection

def backup_database(backup_dir: str = "backups") -> Tuple[bool, str]:
    """
    Create a backup of the database.
    
    Args:
        backup_dir: Directory to store backups
        
    Returns:
        Tuple of (success, backup_path or error_message)
    """
    try:
        global db_connection
        
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        # Get the database path
        db_path = db_connection.execute("PRAGMA database_list").fetchone()[2]
        
        # Create a backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.sqlite3"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Close the connection temporarily
        db_connection.close()
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Reopen the connection
        db_connection = sqlite3.connect(db_path)
        db_connection.row_factory = sqlite3.Row
        
        logger.info(f"Database backed up to {backup_path}")
        return True, backup_path
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False, str(e)

def setup_database_connection(db_path: str) -> bool:
    """
    Set up a connection to the SQLite database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if connection was successful, False otherwise
    """
    global db_connection
    db_connection = None
    
    logger.info(f"Setting up database connection to {db_path}")
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        
        # Check if this is a relative path and the file might be in the app directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        app_root = os.path.dirname(app_dir)
        alternative_path = os.path.join(app_root, os.path.basename(db_path))
        
        if os.path.exists(alternative_path):
            logger.info(f"Found database at alternative path: {alternative_path}")
            db_path = alternative_path
        else:
            logger.error("Database file not found at alternative path either")
            QMessageBox.critical(
                None, 
                "Database Error",
                f"Database file not found at {db_path}.\n\n"
                "Please make sure the ePetCare web application is properly installed "
                "and the database file exists.\n\n"
                "You can also manually specify the database location in the config.json file."
            )
            return False
    
    try:
        # Connect to the SQLite database with timeout to handle locking issues
        logger.debug(f"Attempting to connect to database at: {db_path}")
        db_connection = sqlite3.connect(db_path, timeout=30.0)  # 30 second timeout
        db_connection.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency
        try:
            db_connection.execute("PRAGMA journal_mode=WAL;")
            db_connection.execute("PRAGMA synchronous=NORMAL;")
            db_connection.execute("PRAGMA busy_timeout=30000;")  # 30 seconds
            logger.debug("SQLite WAL mode enabled for better concurrency")
        except sqlite3.Error as e:
            logger.warning(f"Failed to set PRAGMA settings: {e}")
        
        # Test connection
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        required_tables = [
            'auth_user', 'clinic_owner', 'clinic_pet', 'clinic_appointment',
            'clinic_medicalrecord', 'clinic_prescription'
        ]
        
        table_names = [table['name'] for table in tables]
        logger.debug(f"Found tables: {', '.join(table_names)}")
        
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            logger.error(f"Missing required tables: {', '.join(missing_tables)}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"The database is missing required tables: {', '.join(missing_tables)}.\n\n"
                "Please make sure you are connecting to the correct ePetCare database."
            )
            db_connection.close()
            db_connection = None
            return False
                
        # Check if vet_veterinarian table exists, if not it might be a new installation
        if 'vet_veterinarian' not in table_names:
            logger.warning("vet_veterinarian table not found, attempting to create it")
            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS vet_veterinarian (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    full_name TEXT NOT NULL,
                    specialization TEXT,
                    license_number TEXT,
                    phone TEXT,
                    bio TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES auth_user (id)
                )
                """)
                db_connection.commit()
                logger.info("Created vet_veterinarian table successfully")
            except sqlite3.Error as e:
                logger.error(f"Failed to create vet_veterinarian table: {e}")
                # Continue anyway, as this might not be critical
        
        # Check if vet_notification table exists, if not create it
        if 'vet_notification' not in table_names:
            logger.warning("vet_notification table not found, attempting to create it")
            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS vet_notification (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veterinarian_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (veterinarian_id) REFERENCES vet_veterinarian (id)
                )
                """)
                db_connection.commit()
                logger.info("Created vet_notification table successfully")
            except sqlite3.Error as e:
                logger.error(f"Failed to create vet_notification table: {e}")
                # Continue anyway, as this might not be critical
                
        # Update the config with the successful path
        from utils.config import load_config, save_config
        config = load_config()
        if config['database']['path'] != db_path:
            config['database']['path'] = db_path
            save_config(config)
            
        logger.info("Database connection established successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        error_message = str(e)
        solution = "Please make sure the database file is accessible and not corrupted."
        
        # Provide more specific error messages for common issues
        if "database is locked" in error_message.lower():
            solution = "The database is locked by another process. Please close any other applications that might be using the database and try again."
        elif "no such table" in error_message.lower():
            solution = "The database schema appears to be incomplete or corrupted. Please check that you're using the correct database file."
        elif "unable to open database file" in error_message.lower():
            solution = "Unable to open the database file. Please check file permissions and make sure the path is correct."
            
        QMessageBox.critical(
            None,
            "Database Error",
            f"Failed to connect to the database: {error_message}\n\n{solution}"
        )
        return False


class DatabaseManager:
    """
    Manager for database operations.
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize the database manager.
        
        Args:
            db_connection: Optional SQLite connection object
        """
        self.db_connection = db_connection or globals().get('db_connection')
        if not self.db_connection:
            raise ValueError("No database connection available")
    
    def fetch_by_id(self, table: str, id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Fetch a record by ID.
        
        Args:
            table: Table name
            id: Record ID
            
        Returns:
            Tuple of (success, record)
            - success: True if record was found, False otherwise
            - record: Dictionary with record data if found, None otherwise
        """
        try:
            query = f"SELECT * FROM {table} WHERE id = ?"
            cursor = self.db_connection.cursor()
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            
            if result:
                return True, dict(result)
            else:
                return False, None
        except sqlite3.Error as e:
            logger.error(f"Error fetching from {table}: {e}")
            return False, None
    
    def fetch_all(self, table: str, conditions: Dict[str, Any] = None, 
                  order_by: str = None, limit: int = None) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Fetch all records from a table with optional filtering, ordering, and limiting.
        
        Args:
            table: Table name
            conditions: Dictionary of column names and values for WHERE clause
            order_by: Column name(s) for ORDER BY clause
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (success, records)
            - success: True if query executed successfully, False otherwise
            - records: List of dictionaries with record data if successful, empty list otherwise
        """
        try:
            query = f"SELECT * FROM {table}"
            params = []
            
            # Add WHERE clause if conditions are provided
            if conditions:
                where_clauses = []
                for column, value in conditions.items():
                    where_clauses.append(f"{column} = ?")
                    params.append(value)
                query += f" WHERE {' AND '.join(where_clauses)}"
            
            # Add ORDER BY clause if specified
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Add LIMIT clause if specified
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = self.db_connection.cursor()
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            return True, results
        except sqlite3.Error as e:
            logger.error(f"Error fetching all from {table}: {e}")
            return False, []
    
    def execute_query(self, query: str, params: tuple = (), max_retries: int = 3, retry_delay: float = 1.0) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Execute a SQL query and return the results as a list of dictionaries.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            max_retries: Maximum number of retries for locked database
            retry_delay: Delay between retries in seconds
            
        Returns:
            Tuple of (success, results)
            - success: True if query executed successfully, False otherwise
            - results: List of dictionaries with query results if successful, empty list otherwise
        """
        retry_count = 0
        while True:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                return True, results
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"Database locked, retrying ({retry_count}/{max_retries})...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Database error: {e}")
                    return False, []
    
    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """
        Execute a non-query SQL statement (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL statement to execute
            params: Parameters for the statement
            
        Returns:
            Number of rows affected
        """
        cursor = self.db_connection.cursor()
        cursor.execute(query, params)
        self.db_connection.commit()
        return cursor.rowcount
    
    def insert(self, table: str, data: Dict[str, Any]) -> Tuple[bool, Union[int, str]]:
        """
        Insert data into a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            
        Returns:
            Tuple of (success, id_or_error_message)
            - success: True if insertion was successful, False otherwise
            - id_or_error_message: ID of the inserted row if successful, error message otherwise
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = tuple(data.values())
            
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            cursor = self.db_connection.cursor()
            cursor.execute(query, values)
            self.db_connection.commit()
            
            return True, cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error inserting into {table}: {e}")
            return False, str(e)
    
    def update(self, table: str, data: Dict[str, Any], id: int) -> Tuple[bool, Union[int, str]]:
        """
        Update data in a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            id: ID of the row to update
            
        Returns:
            Tuple of (success, rows_affected or error_message)
        """
        set_clause = ', '.join([f"{column} = ?" for column in data.keys()])
        values = tuple(data.values()) + (id,)
        
        query = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, values)
            self.db_connection.commit()
            return True, cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error updating {table}: {e}")
            return False, str(e)
    
    def delete(self, table: str, id: int) -> Tuple[bool, Union[int, str]]:
        """
        Delete a row from a table.
        
        Args:
            table: Table name
            id: ID of the row to delete
            
        Returns:
            Tuple of (success, rows_affected or error_message)
        """
        query = f"DELETE FROM {table} WHERE id = ?"
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, (id,))
            self.db_connection.commit()
            return True, cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error deleting from {table}: {e}")
            return False, str(e)
    
    def backup_database(self, backup_dir: str = "backups") -> Tuple[bool, str]:
        """
        Create a backup of the database.
        
        Args:
            backup_dir: Directory to store backups
            
        Returns:
            Tuple of (success, backup_path or error_message)
        """
        try:
            # Ensure backup directory exists
            os.makedirs(backup_dir, exist_ok=True)
            
            # Get the database path
            db_path = self.db_connection.execute("PRAGMA database_list").fetchone()[2]
            
            # Create a backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.sqlite3"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Close the connection temporarily
            self.db_connection.close()
            
            # Copy the database file
            shutil.copy2(db_path, backup_path)
            
            # Reopen the connection
            self.db_connection = sqlite3.connect(db_path)
            self.db_connection.row_factory = sqlite3.Row
            
            logger.info(f"Database backed up to {backup_path}")
            return True, backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False, str(e)