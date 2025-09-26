"""
Login dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QIcon
import sys
import os
import importlib.util
import logging

logger = logging.getLogger('epetcare')

# Special handling for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    logger.debug("login_dialog.py: Using special import handling for frozen app")
    
    try:
        # Try normal imports first
        from models.data_access import UserDataAccess, VeterinarianDataAccess
        try:
            from utils.pg_db import get_connection
        except ImportError:
            from utils.database import get_connection  # fallback (legacy)
        from views.register_dialog import RegisterDialog
        logger.debug("Successfully imported modules in login_dialog.py")
    except ImportError as e:
        logger.error(f"Import error in login_dialog.py: {e}")
        
        # Get the base directory
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import directly from files
        try:
            # Import models.data_access
            try:
                from models.data_access import UserDataAccess, VeterinarianDataAccess
            except ImportError:
                data_access_path = os.path.join(base_dir, 'models', 'data_access.py')
                if os.path.exists(data_access_path):
                    spec = importlib.util.spec_from_file_location("models.data_access", data_access_path)
                    data_access_module = importlib.util.module_from_spec(spec)
                    sys.modules['models.data_access'] = data_access_module
                    spec.loader.exec_module(data_access_module)
                    UserDataAccess = data_access_module.UserDataAccess
                    VeterinarianDataAccess = data_access_module.VeterinarianDataAccess
                    logger.debug(f"Imported UserDataAccess and VeterinarianDataAccess from {data_access_path}")
                else:
                    logger.error(f"data_access.py not found at {data_access_path}")
            
            # Import connection getter (prefer pg_db)
            try:
                from utils.pg_db import get_connection
            except ImportError:
                try:
                    from utils.database import get_connection
                except ImportError:
                    get_connection = lambda: None  # placeholder
            
            # Fallback manual load of database.py if still needed
            if 'get_connection' not in locals() or get_connection is None:
                database_path = os.path.join(base_dir, 'utils', 'database.py')
                if os.path.exists(database_path):
                    spec = importlib.util.spec_from_file_location("utils.database", database_path)
                    database_module = importlib.util.module_from_spec(spec)
                    sys.modules['utils.database'] = database_module
                    spec.loader.exec_module(database_module)
                    get_connection = database_module.get_connection
                    logger.debug(f"Imported get_connection from {database_path}")
                else:
                    logger.error(f"database.py not found at {database_path}")
            
            # Import views.register_dialog
            try:
                from views.register_dialog import RegisterDialog
            except ImportError:
                register_dialog_path = os.path.join(base_dir, 'views', 'register_dialog.py')
                if os.path.exists(register_dialog_path):
                    spec = importlib.util.spec_from_file_location("views.register_dialog", register_dialog_path)
                    register_dialog_module = importlib.util.module_from_spec(spec)
                    sys.modules['views.register_dialog'] = register_dialog_module
                    spec.loader.exec_module(register_dialog_module)
                    RegisterDialog = register_dialog_module.RegisterDialog
                    logger.debug(f"Imported RegisterDialog from {register_dialog_path}")
                else:
                    logger.error(f"register_dialog.py not found at {register_dialog_path}")
                    
        except Exception as e:
            logger.error(f"Error importing modules in login_dialog.py: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
else:
    # Running as a normal Python script
    from models.data_access import UserDataAccess, VeterinarianDataAccess
    try:
        from utils.pg_db import get_connection
    except ImportError:
        from utils.database import get_connection
    from views.register_dialog import RegisterDialog


class LoginDialog(QDialog):
    """Login dialog for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data_access = UserDataAccess()
        self.vet_data_access = VeterinarianDataAccess()
        self.user = None
        self.veterinarian = None
        
        self.setWindowTitle("ePetCare Vet Desktop - Login")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("ePetCare Vet Desktop")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        subtitle_label = QLabel("Veterinarian Login")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Login form
        login_group = QGroupBox("Login")
        login_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        login_layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        login_layout.addRow("Password:", self.password_edit)
        
        login_group.setLayout(login_layout)
        layout.addWidget(login_group)
        
        # Register link
        register_layout = QHBoxLayout()
        register_label = QLabel("Don't have an account?")
        register_layout.addWidget(register_label)
        
        self.register_button = QPushButton("Register")
        self.register_button.setFlat(True)
        self.register_button.setCursor(Qt.PointingHandCursor)
        self.register_button.clicked.connect(self.show_register_dialog)
        register_layout.addWidget(self.register_button)
        
        register_layout.addStretch()
        layout.addLayout(register_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.try_login)
        button_layout.addWidget(self.login_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Set focus to username field
        self.username_edit.setFocus()
    
    def try_login(self):
        """Try to log in with the provided credentials"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Please enter both username and password."
            )
            return
        
        # Check if database connection is available
        if not get_connection():
            QMessageBox.critical(
                self,
                "Database Error",
                "No database connection available. Please restart the application."
            )
            return
        
        # Authenticate user
        self.user = self.user_data_access.authenticate(username, password)
        
        if not self.user:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Invalid username or password."
            )
            return
        
        # Check if user is a veterinarian
        self.veterinarian = self.vet_data_access.get_by_user_id(self.user.id)
        
        if not self.veterinarian:
            QMessageBox.warning(
                self,
                "Access Denied",
                "This user is not registered as a veterinarian."
            )
            self.user = None
            return
        
        # Login successful
        self.accept()
    
    def get_user(self):
        """Get the authenticated user"""
        return self.user
    
    def get_veterinarian(self):
        """Get the authenticated veterinarian"""
        return self.veterinarian
    
    def show_register_dialog(self):
        """Show the registration dialog"""
        dialog = RegisterDialog(self)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            # If registration was successful, auto-fill the login form
            user_id = dialog.get_user_id()
            if user_id:
                user = self.user_data_access.get_by_id(user_id)
                if user:
                    self.username_edit.setText(user.username)
                    # Focus on password field
                    self.password_edit.setFocus()
