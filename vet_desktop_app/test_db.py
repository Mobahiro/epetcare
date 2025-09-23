#!/usr/bin/env python3
"""
Database test script for the ePetCare Vet Desktop application.
This script tests the database connection and displays information about the database.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('epetcare_db_test')

def test_database_connection(db_path):
    """Test the database connection"""
    logger.info(f"Testing database connection to: {db_path}")
    
    # Check if the file exists
    if not os.path.exists(db_path):
        logger.error(f"Database file does not exist at: {db_path}")
        return False
    
    # Check if the file is empty
    if os.path.getsize(db_path) == 0:
        logger.error(f"Database file is empty: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.info("Successfully connected to the database")
        
        # Get the list of tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.error("Database has no tables")
            return False
        
        # Log the tables
        logger.info(f"Database has {len(tables)} tables:")
        for table in tables:
            table_name = table['name']
            logger.info(f"  - {table_name}")
            
            # Get the number of rows in the table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                logger.info(f"    - {row_count} rows")
                
                # Get the column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                logger.info(f"    - Columns: {', '.join(col['name'] for col in columns)}")
                
                # Show a sample row if available
                if row_count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                    sample_row = cursor.fetchone()
                    if sample_row:
                        logger.info(f"    - Sample row: {dict(sample_row)}")
            except sqlite3.Error as e:
                logger.error(f"Error getting information for table {table_name}: {e}")
        
        # Close the connection
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return False

def find_database():
    """Find the database file"""
    logger.info("Searching for database file...")
    
    # List of possible locations
    possible_locations = [
        "db.sqlite3",
        "data/db.sqlite3",
        "../db.sqlite3",
        "dist/ePetCare_Vet_Desktop/db.sqlite3",
        "dist/ePetCare_Vet_Desktop/data/db.sqlite3",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite3"),
        "C:/Users/Shiro/epetcare/db.sqlite3",
        "C:/Users/Shiro/epetcare/vet_desktop_app/data/db.sqlite3",
        "C:/Users/Shiro/epetcare/vet_desktop_app/dist/ePetCare_Vet_Desktop/db.sqlite3",
        "C:/Users/Shiro/epetcare/vet_desktop_app/dist/ePetCare_Vet_Desktop/data/db.sqlite3"
    ]
    
    # Check each location
    for location in possible_locations:
        if os.path.exists(location):
            logger.info(f"Found database at: {location}")
            if test_database_connection(location):
                logger.info(f"Successfully connected to database at: {location}")
                return location
    
    logger.error("Could not find a valid database file")
    return None

if __name__ == "__main__":
    logger.info("ePetCare Vet Desktop Database Test")
    logger.info(f"Current directory: {os.getcwd()}")
    
    # If a path is provided as an argument, use that
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        test_database_connection(db_path)
    else:
        # Otherwise, try to find the database
        find_database()
