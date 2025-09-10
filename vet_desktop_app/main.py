#!/usr/bin/env python3
"""
ePetCare Vet Desktop Application
--------------------------------
A standalone desktop application for veterinarians to access the ePetCare system.
This application connects to the same database as the ePetCare web application.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont
from views.main_window import MainWindow
from utils.database import setup_database_connection
from utils.config import load_config


def main():
    """Main entry point for the application"""
    # Create application instance
    app = QApplication(sys.argv)
    app.setApplicationName("ePetCare Vet Desktop")
    app.setOrganizationName("ePetCare")
    app.setOrganizationDomain("epetcare.local")

    # Set up fonts
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)

    # Apply stylesheet
    style_path = os.path.join(os.path.dirname(__file__), 'resources', 'style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r') as f:
            app.setStyleSheet(f.read())

    # Load configuration
    config = load_config()
    
    # Setup database connection
    db_path = config.get('database', {}).get('path', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3'))
    if not setup_database_connection(db_path):
        sys.exit(1)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
