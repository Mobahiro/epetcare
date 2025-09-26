#!/usr/bin/env python3
"""
ePetCare Vet Desktop Application
--------------------------------
A standalone desktop application for veterinarians to access the ePetCare system.
This application connects to the same database as the ePetCare web application.
"""

import sys
import os
import traceback
import logging
from pathlib import Path

# Set up logging
DEBUG_MODE = os.environ.get('EPETCARE_DEBUG') == '1'
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO

# Create logs directory if it doesn't exist
logs_dir = Path('logs')
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('epetcare')

# Log startup information
logger.info("Starting ePetCare Vet Desktop Application")
logger.debug(f"Python version: {sys.version}")
logger.debug(f"Python executable: {sys.executable}")
logger.debug(f"Current directory: {os.getcwd()}")
logger.debug(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
logger.debug(f"Debug mode: {'Enabled' if DEBUG_MODE else 'Disabled'}")

try:
    # Add the current directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        logger.debug(f"Added {current_dir} to Python path")
    
    # Log Python path
    logger.debug("Python path:")
    for path in sys.path:
        logger.debug(f"  - {path}")
    
    # Import and use the module finder to ensure all modules are importable
    try:
        logger.debug("Using module finder to ensure modules are importable...")
        from module_finder import ensure_modules_importable
        ensure_modules_importable()
    except ImportError:
        logger.warning("Could not import module_finder. Continuing without it.")
    
    # Import required modules
    logger.debug("Importing required modules...")
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QFont
    
    # Try importing application modules
    try:
        # Import from the top-level packages first
        import views
        import utils
        import models
        logger.debug("Successfully imported top-level packages")
        
        # Now import specific modules
        from views.main_window import MainWindow
        from utils.database import setup_database_connection
        from utils.config import load_config
        logger.debug("Successfully imported application modules")
        
        # Verify models.data_access is importable
        try:
            import models.data_access
            logger.debug("Successfully imported models.data_access")
        except ImportError as e:
            logger.error(f"Failed to import models.data_access: {e}")
            # Try a direct import from file
            try:
                import importlib.util
                data_access_path = os.path.join(current_dir, 'models', 'data_access.py')
                if os.path.exists(data_access_path):
                    logger.debug(f"Attempting to load models.data_access from {data_access_path}")
                    spec = importlib.util.spec_from_file_location("models.data_access", data_access_path)
                    data_access_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(data_access_module)
                    sys.modules['models.data_access'] = data_access_module
                    logger.debug("Successfully loaded models.data_access from file")
                else:
                    logger.error(f"Could not find data_access.py at {data_access_path}")
            except Exception as e2:
                logger.error(f"Failed to load models.data_access from file: {e2}")
                logger.error(traceback.format_exc())
                raise
    except ImportError as e:
        logger.error(f"Failed to import application modules: {e}")
        logger.error(traceback.format_exc())
        
        # If running as executable, show error message
        if getattr(sys, 'frozen', False):
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Import Error",
                f"Failed to import application modules: {e}\n\n"
                "This is likely due to a problem with the application installation.\n"
                "Please try reinstalling the application."
            )
            sys.exit(1)
        else:
            # Re-raise the exception if running from source
            raise
except Exception as e:
    logger.error(f"Error during startup: {e}")
    logger.error(traceback.format_exc())
    
    # If we can't even import QMessageBox, just print to stderr
    print(f"Error during startup: {e}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)


def main():
    """Main entry point for the application"""
    try:
        logger.info("Initializing application...")
        
        # Create application instance
        app = QApplication(sys.argv)
        app.setApplicationName("ePetCare Vet Desktop")
        app.setOrganizationName("ePetCare")
        app.setOrganizationDomain("epetcare.local")
        
        # Log application info
        logger.debug(f"Application name: {app.applicationName()}")
        logger.debug(f"Organization name: {app.organizationName()}")
        logger.debug(f"Organization domain: {app.organizationDomain()}")

        # Set up fonts and theme
        try:
            # Import theme manager
            from utils.theme_manager import apply_theme, update_font_size
            
            # Apply theme and font size
            theme_applied = apply_theme(app)
            font_updated = update_font_size(app)
            
            logger.debug(f"Theme applied: {theme_applied}, Font updated: {font_updated}")
        except Exception as e:
            logger.error(f"Error applying theme: {e}")
            
            # Fallback to default font
            default_font = QFont("Segoe UI", 10)
            app.setFont(default_font)
            logger.debug(f"Default font set: {default_font.family()} {default_font.pointSize()}")

        # Apply stylesheet - try multiple possible paths
        style_paths = [
            os.path.join(os.path.dirname(__file__), 'resources', 'style.qss'),
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources', 'style.qss')),
        ]
        
        # If running as frozen app, add more paths
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
                style_paths.append(os.path.join(base_dir, 'resources', 'style.qss'))
                style_paths.append(os.path.join(base_dir, 'style.qss'))
        
        # Log all paths we're checking
        for path in style_paths:
            logger.debug(f"Checking for stylesheet at: {path}")
        
        # Try each path
        stylesheet_loaded = False
        for style_path in style_paths:
            if os.path.exists(style_path):
                try:
                    with open(style_path, 'r') as f:
                        stylesheet = f.read()
                        app.setStyleSheet(stylesheet)
                        logger.debug(f"Stylesheet applied successfully from {style_path}")
                        stylesheet_loaded = True
                        break
                except Exception as e:
                    logger.error(f"Error loading stylesheet from {style_path}: {e}")
        
        if not stylesheet_loaded:
            logger.warning("Stylesheet not found in any of the checked locations")

        # Load configuration
        logger.debug("Loading configuration...")
        config = load_config()
        logger.debug(f"Configuration loaded: {config}")
        
        # Setup PostgreSQL connection (new unified path)
        logger.debug("Setting up PostgreSQL connection...")
        pg_cfg = config.get('postgres') or {}
        if not pg_cfg:
            logger.error("No 'postgres' section found in config.json; cannot connect.")
            QMessageBox.critical(None, "Configuration Error", "config.json is missing the 'postgres' section.")
            sys.exit(1)
        try:
            from utils.pg_db import setup_postgres_connection
        except ImportError:
            QMessageBox.critical(None, "Missing Dependency", "psycopg2 not installed. Install requirements and retry.")
            sys.exit(1)

        if not setup_postgres_connection(pg_cfg):
            QMessageBox.critical(
                None,
                "Database Error",
                "Failed to connect to PostgreSQL.\n\nFill in host, database, user, password (or database_url) in config.json under 'postgres'.\nYou can copy these from the Render PostgreSQL instance (Connections tab)."
            )
            sys.exit(1)
        logger.info("Connected to PostgreSQL successfully")

        # Basic schema sanity check (auth_user is a core Django table)
        try:
            from utils.pg_db import get_connection as _pg_get_conn
            conn = _pg_get_conn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_user'")
                if cur.fetchone() is None:
                    logger.error("Core table auth_user not found. Django migrations likely not run on this database.")
                    QMessageBox.critical(
                        None,
                        "Schema Missing",
                        "The PostgreSQL database is empty or migrations have not been run.\n\n"
                        "Run Django migrations first:\n"
                        "1. Set DATABASE_URL to this database.\n"
                        "2. Run: python manage.py migrate\n\n"
                        "After migrations complete, restart the desktop app."
                    )
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Schema check failed: {e}")
        
        # Create and show the main window
        logger.info("Creating main window...")
        window = MainWindow()
        window.show()
        logger.info("Application started successfully")
        
        # Start the event loop
        return app.exec()
        
    except Exception as e:
        logger.critical(f"Unhandled exception in main(): {e}")
        logger.critical(traceback.format_exc())
        
        # Show error message to user
        try:
            if 'app' in locals():
                QMessageBox.critical(
                    None,
                    "Application Error",
                    f"An unhandled error occurred:\n\n{str(e)}\n\n"
                    "Please check the log file for details."
                )
            else:
                # Create a minimal application to show the error
                minimal_app = QApplication(sys.argv)
                QMessageBox.critical(
                    None,
                    "Application Error",
                    f"An unhandled error occurred:\n\n{str(e)}\n\n"
                    "Please check the log file for details."
                )
        except Exception:
            # If we can't show a GUI error, print to stderr
            print(f"Critical error: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
        
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)
