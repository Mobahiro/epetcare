"""
DEPRECATED: PostgreSQL Sync Utility for ePetCare

This module previously provided functions to synchronize data between the local SQLite database
and the remote PostgreSQL database on Render.com.

It is now DEPRECATED and should not be used, as the application has been migrated to use 
PostgreSQL directly via utils.pg_db. This file is kept temporarily for reference only and
will be removed in a future update.
"""

import os
import json
import logging
import sqlite3
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='postgres_sync.log',
    filemode='a'
)
logger = logging.getLogger('postgres_sync')

def load_config():
    """Load the configuration from config.json"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def get_postgres_connection():
    """
    Get a connection to the PostgreSQL database
    """
    config = load_config()
    pg_config = config.get('db_sync', {}).get('postgres', {})
    
    if not pg_config.get('enabled', False):
        logger.error("PostgreSQL sync is not enabled in config")
        return None
    
    try:
        connection = psycopg2.connect(
            host=pg_config.get('host'),
            port=pg_config.get('port', 5432),
            database=pg_config.get('database'),
            user=pg_config.get('username'),
            password=pg_config.get('password')
        )
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return None

def get_sqlite_connection():
    """
    Get a connection to the local SQLite database
    """
    config = load_config()
    db_path = config.get('database', {}).get('path')
    
    if not db_path:
        logger.error("SQLite database path not configured")
        return None
    
    try:
        return sqlite3.connect(db_path)
    except Exception as e:
        logger.error(f"Failed to connect to SQLite: {e}")
        return None

def sync_table(table_name, primary_key="id"):
    """
    Synchronize a table between SQLite and PostgreSQL
    """
    logger.info(f"Starting synchronization of table {table_name}")
    
    # Get connections
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    if not sqlite_conn or not postgres_conn:
        logger.error("Failed to establish database connections")
        return False
    
    try:
        # Get SQLite data
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in sqlite_cursor.description]
        sqlite_data = sqlite_cursor.fetchall()
        
        # Get PostgreSQL data
        postgres_cursor = postgres_conn.cursor()
        postgres_cursor.execute(sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.Identifier(table_name)
        ))
        postgres_data = postgres_cursor.fetchall()
        
        # Convert to dictionaries for easier comparison
        sqlite_records = {row[columns.index(primary_key)]: dict(zip(columns, row)) for row in sqlite_data}
        postgres_records = {row[columns.index(primary_key)]: dict(zip(columns, row)) for row in postgres_data}
        
        # Find records to insert, update, and delete
        all_keys = set(sqlite_records.keys()) | set(postgres_records.keys())
        
        for key in all_keys:
            # Record exists in SQLite but not in PostgreSQL (INSERT)
            if key in sqlite_records and key not in postgres_records:
                record = sqlite_records[key]
                columns_to_insert = [col for col in columns if col in record]
                postgres_cursor.execute(
                    sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                        sql.Identifier(table_name),
                        sql.SQL(', ').join(map(sql.Identifier, columns_to_insert)),
                        sql.SQL(', ').join(sql.Placeholder() * len(columns_to_insert))
                    ),
                    [record[col] for col in columns_to_insert]
                )
                logger.info(f"Inserted record with {primary_key}={key} into PostgreSQL")
            
            # Record exists in both databases (UPDATE if different)
            elif key in sqlite_records and key in postgres_records:
                sqlite_record = sqlite_records[key]
                postgres_record = postgres_records[key]
                
                # Check if records are different
                if any(sqlite_record[col] != postgres_record[col] for col in columns):
                    # Build the SET part of the query
                    update_values = [
                        (col, sqlite_record[col]) 
                        for col in columns 
                        if col != primary_key and col in sqlite_record
                    ]
                    
                    if update_values:
                        postgres_cursor.execute(
                            sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                                sql.Identifier(table_name),
                                sql.SQL(', ').join(
                                    sql.SQL("{} = %s").format(sql.Identifier(col)) 
                                    for col, _ in update_values
                                ),
                                sql.Identifier(primary_key)
                            ),
                            [val for _, val in update_values] + [key]
                        )
                        logger.info(f"Updated record with {primary_key}={key} in PostgreSQL")
            
            # Record exists in PostgreSQL but not in SQLite (DELETE)
            # Uncomment if you want to delete records that are not in SQLite
            # elif key in postgres_records and key not in sqlite_records:
            #     postgres_cursor.execute(
            #         sql.SQL("DELETE FROM {} WHERE {} = %s").format(
            #             sql.Identifier(table_name),
            #             sql.Identifier(primary_key)
            #         ),
            #         [key]
            #     )
            #     logger.info(f"Deleted record with {primary_key}={key} from PostgreSQL")
        
        # Commit the changes
        postgres_conn.commit()
        logger.info(f"Synchronization of table {table_name} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to synchronize table {table_name}: {e}")
        postgres_conn.rollback()
        return False
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if postgres_conn:
            postgres_conn.close()

def sync_all_tables():
    """
    Synchronize all tables between SQLite and PostgreSQL
    """
    # Define the tables to sync and their primary keys
    tables = [
        ("auth_user", "id"),
        ("clinic_owner", "id"),
        ("clinic_pet", "id"),
        ("clinic_appointment", "id"),
        ("vet_veterinarian", "id"),
        ("vet_appointment", "id"),
        ("vet_prescription", "id"),
        ("vet_portal_notification", "id"),
    ]
    
    success_count = 0
    for table_name, primary_key in tables:
        if sync_table(table_name, primary_key):
            success_count += 1
    
    logger.info(f"Synchronized {success_count} out of {len(tables)} tables")
    return success_count == len(tables)

def trigger_deploy_hook():
    """
    Trigger the deploy hook on Render
    """
    import requests
    
    config = load_config()
    deploy_hook = config.get('remote_database', {}).get('deploy_hook')
    
    if not deploy_hook:
        logger.error("Deploy hook URL not configured")
        return False
    
    try:
        response = requests.post(deploy_hook)
        if response.status_code == 200:
            logger.info("Successfully triggered deploy hook")
            return True
        else:
            logger.error(f"Failed to trigger deploy hook: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error triggering deploy hook: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting PostgreSQL synchronization")
    if sync_all_tables():
        logger.info("All tables synchronized successfully")
        trigger_deploy_hook()
    else:
        logger.error("Failed to synchronize all tables")