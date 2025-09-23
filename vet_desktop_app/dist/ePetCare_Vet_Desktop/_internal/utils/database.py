"""
Database utilities for the ePetCare Vet Desktop application.
"""

import os
import sqlite3
import shutil
import datetime
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject, Signal

# Global database connection
db_connection = None


def setup_database_connection(db_path):
    """Setup the database connection"""
    global db_connection
    import logging
    logger = logging.getLogger('epetcare')
    
    # Normalize path for Windows
    db_path = os.path.normpath(db_path)
    logger.debug(f"Setting up database connection with path: {db_path}")
    
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        logger.warning(f"Database not found or empty at {db_path}")
        # Try to find the database in common locations
        possible_locations = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'db.sqlite3'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db.sqlite3')
        ]
        
        # If running as PyInstaller bundle, add more possible locations
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
            possible_locations.extend([
                os.path.join(base_dir, 'db.sqlite3'),
                os.path.join(base_dir, 'data', 'db.sqlite3'),
                os.path.join(os.path.dirname(base_dir), 'db.sqlite3'),
                os.path.join(os.path.dirname(base_dir), 'data', 'db.sqlite3'),
                os.path.join(os.path.dirname(os.path.dirname(base_dir)), 'db.sqlite3')
            ])
        
        # Log all possible locations
        logger.debug("Searching for database in the following locations:")
        for path in possible_locations:
            logger.debug(f"  - {path}")
        
        found = False
        for path in possible_locations:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                db_path = path
                logger.info(f"Found database at: {db_path}")
                found = True
                break
                
        if not found:
            logger.error("Database file not found in any common location")
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
        # Connect to the SQLite database
        db_connection = sqlite3.connect(db_path)
        db_connection.row_factory = sqlite3.Row
        
        # Test connection
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        required_tables = [
            'auth_user', 'clinic_owner', 'clinic_pet', 'clinic_appointment',
            'clinic_medicalrecord', 'clinic_prescription', 'vet_veterinarian'
        ]
        
        table_names = [table['name'] for table in tables]
        
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            QMessageBox.critical(
                None,
                "Database Error",
                f"The database is missing required tables: {', '.join(missing_tables)}.\n\n"
                "Please make sure you are connecting to the correct ePetCare database."
            )
            db_connection.close()
            db_connection = None
            return False
                
        # Update the config with the successful path
        from utils.config import load_config, save_config
        config = load_config()
        if config['database']['path'] != db_path:
            config['database']['path'] = db_path
            save_config(config)
            
        return True
        
    except sqlite3.Error as e:
        QMessageBox.critical(
            None,
            "Database Error",
            f"Failed to connect to database: {str(e)}\n\n"
            "Please make sure the database file is accessible and not corrupted."
        )
        if db_connection:
            db_connection.close()
            db_connection = None
        return False


def get_connection():
    """Get the database connection"""
    global db_connection
    return db_connection


def close_connection():
    """Close the database connection"""
    global db_connection
    if db_connection:
        db_connection.close()
        db_connection = None


def backup_database(backup_dir=None):
    """Create a backup of the database"""
    global db_connection
    
    if not db_connection:
        return False, "No database connection"
    
    try:
        # Get the database file path
        db_path = db_connection.execute("PRAGMA database_list").fetchone()[2]
        
        # Create backup directory if it doesn't exist
        if not backup_dir:
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"epetcare_backup_{timestamp}.sqlite3")
        
        # Create backup
        shutil.copy2(db_path, backup_file)
        
        return True, backup_file
        
    except Exception as e:
        return False, str(e)


class DatabaseManager(QObject):
    """Database manager class for handling database operations"""
    
    sync_started = Signal()
    sync_completed = Signal(bool, str)  # Success, Message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offline_changes = []
    
    def execute_query(self, query, params=None):
        """Execute a query and return the results"""
        conn = get_connection()
        if not conn:
            return False, "No database connection"
        
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
                return True, cursor.lastrowid
            else:
                return True, cursor.fetchall()
                
        except sqlite3.Error as e:
            return False, str(e)
    
    def fetch_all(self, table, conditions=None, order_by=None, limit=None):
        """Fetch all records from a table with optional conditions"""
        query = f"SELECT * FROM {table}"
        params = []
        
        if conditions:
            query += " WHERE "
            clauses = []
            for key, value in conditions.items():
                clauses.append(f"{key} = ?")
                params.append(value)
            query += " AND ".join(clauses)
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, params)
    
    def fetch_by_id(self, table, id_value, id_column='id'):
        """Fetch a record by ID"""
        query = f"SELECT * FROM {table} WHERE {id_column} = ?"
        success, result = self.execute_query(query, (id_value,))
        
        if success and result:
            return True, result[0]
        elif success:
            return False, "Record not found"
        else:
            return False, result
    
    def insert(self, table, data):
        """Insert a record into a table"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        return self.execute_query(query, tuple(data.values()))
    
    def update(self, table, data, id_value, id_column='id'):
        """Update a record in a table"""
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {id_column} = ?"
        
        params = list(data.values())
        params.append(id_value)
        
        return self.execute_query(query, params)
    
    def delete(self, table, id_value, id_column='id'):
        """Delete a record from a table"""
        query = f"DELETE FROM {table} WHERE {id_column} = ?"
        return self.execute_query(query, (id_value,))
    
    def add_offline_change(self, change_type, model_type, model_id, data):
        """Add an offline change to be synced later"""
        self.offline_changes.append({
            'type': change_type,
            'model': model_type,
            'id': model_id,
            'data': data,
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    def get_offline_changes(self):
        """Get all offline changes"""
        return self.offline_changes
    
    def clear_offline_changes(self):
        """Clear all offline changes"""
        self.offline_changes = []
