"""
PostgreSQL Connection Test

This script tests the connection to the PostgreSQL database on Render.
"""

import json
import os
import sys
import logging
from datetime import datetime

# Ensure the utils directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('postgres_test.log')
    ]
)
logger = logging.getLogger('postgres_test')

def load_config():
    """Load configuration from config.json"""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        if not os.path.exists(config_path):
            logger.error(f"Config file not found at {config_path}")
            return None

        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def test_postgres_connection():
    """Test connection to PostgreSQL"""
    try:
        import psycopg2
        
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return False
        
        pg_config = config.get('db_sync', {}).get('postgres', {})
        if not pg_config:
            logger.error("PostgreSQL configuration not found")
            return False
        
        if not pg_config.get('enabled', False):
            logger.warning("PostgreSQL sync is not enabled in config")
            return False
        
        # Get connection parameters
        host = pg_config.get('host')
        port = pg_config.get('port', 5432)
        database = pg_config.get('database')
        username = pg_config.get('username')
        password = pg_config.get('password')
        
        # Check required parameters
        if not all([host, database, username, password]):
            logger.error("Missing required PostgreSQL connection parameters")
            return False
        
        # Try to connect
        logger.info(f"Attempting to connect to PostgreSQL at {host}:{port}")
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        
        # Check connection is working
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"Connected to PostgreSQL: {version}")
        
        # Check if the tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found tables: {', '.join(tables)}")
        
        # Close connection
        cursor.close()
        connection.close()
        
        return True
    
    except ImportError:
        logger.error("psycopg2 module not installed. Run 'pip install psycopg2-binary'")
        return False
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return False

def test_render_api():
    """Test connection to Render API"""
    try:
        import requests
        
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return False
        
        remote_db = config.get('remote_database', {})
        api_url = remote_db.get('url')
        
        if not api_url:
            logger.error("Remote database URL not configured")
            return False
        
        # Try to connect
        logger.info(f"Attempting to connect to Render API at {api_url}")
        response = requests.get(api_url)
        
        if response.status_code == 200:
            logger.info("Connected to Render API successfully")
            return True
        else:
            logger.error(f"Failed to connect to Render API: {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"Error connecting to Render API: {e}")
        return False

def test_deploy_hook():
    """Test the deploy hook"""
    try:
        import requests
        
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return False
        
        deploy_hook = config.get('remote_database', {}).get('deploy_hook')
        
        if not deploy_hook:
            logger.error("Deploy hook URL not configured")
            return False
        
        # Just check if it's a valid URL
        logger.info(f"Deploy hook URL: {deploy_hook}")
        
        # Don't actually trigger the hook unless requested
        trigger = input("Do you want to trigger the deploy hook? (y/n): ").lower() == 'y'
        
        if trigger:
            response = requests.post(deploy_hook)
            if response.status_code == 200:
                logger.info("Successfully triggered deploy hook")
                return True
            else:
                logger.error(f"Failed to trigger deploy hook: {response.status_code} - {response.text}")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing deploy hook: {e}")
        return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("ePetCare PostgreSQL Connection Test")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    if not config:
        print("Failed to load configuration. Check the log for details.")
        return
    
    # Test PostgreSQL connection
    print("\nTesting PostgreSQL Connection:")
    if test_postgres_connection():
        print("✅ PostgreSQL connection successful")
    else:
        print("❌ PostgreSQL connection failed")
    
    # Test Render API connection
    print("\nTesting Render API Connection:")
    if test_render_api():
        print("✅ Render API connection successful")
    else:
        print("❌ Render API connection failed")
    
    # Test deploy hook
    print("\nTesting Deploy Hook:")
    if test_deploy_hook():
        print("✅ Deploy hook configuration valid")
    else:
        print("❌ Deploy hook configuration invalid")
    
    print("\n" + "=" * 60)
    print("Test completed. See postgres_test.log for details.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\nError: {e}")
    
    input("\nPress Enter to exit...")