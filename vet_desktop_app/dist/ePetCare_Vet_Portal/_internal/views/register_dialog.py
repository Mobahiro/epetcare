"""
Registration dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QIcon
import sys
import os
import logging

logger = logging.getLogger('epetcare')

# Special handling for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    logger.debug("register_dialog.py: Using special import handling for frozen app")
    
    try:
        # Try normal imports first
        from models.data_access import UserDataAccess, VeterinarianDataAccess
        logger.debug("Successfully imported modules in register_dialog.py")
    except ImportError as e:
        logger.error(f"Import error in register_dialog.py: {e}")
        
        # Get the base directory
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import directly from files
        try:
            # Import models.data_access
            data_access_path = os.path.join(base_dir, 'models', 'data_access.py')
            if os.path.exists(data_access_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("models.data_access", data_access_path)
                data_access_module = importlib.util.module_from_spec(spec)
                sys.modules['models.data_access'] = data_access_module
                spec.loader.exec_module(data_access_module)
                UserDataAccess = data_access_module.UserDataAccess
                VeterinarianDataAccess = data_access_module.VeterinarianDataAccess
                logger.debug(f"Imported UserDataAccess and VeterinarianDataAccess from {data_access_path}")
            else:
                logger.error(f"data_access.py not found at {data_access_path}")
                
        except Exception as e:
            logger.error(f"Error importing modules in register_dialog.py: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
else:
    # Running as a normal Python script
    from models.data_access import UserDataAccess, VeterinarianDataAccess


class RegisterDialog(QDialog):
    """Registration dialog for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data_access = UserDataAccess()
        self.vet_data_access = VeterinarianDataAccess()
        self.user_id = None
        
        self.setWindowTitle("ePetCare Vet Desktop - Register")
        self.setMinimumWidth(500)
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
        
        subtitle_label = QLabel("Veterinarian Registration")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # User information form
        user_group = QGroupBox("User Information")
        user_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        user_layout.addRow("Username:", self.username_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email")
        user_layout.addRow("Email:", self.email_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        user_layout.addRow("Password:", self.password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("Confirm your password")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        user_layout.addRow("Confirm Password:", self.confirm_password_edit)
        
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Enter your first name")
        user_layout.addRow("First Name:", self.first_name_edit)
        
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Enter your last name")
        user_layout.addRow("Last Name:", self.last_name_edit)
        
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)
        
        # Veterinarian information form
        vet_group = QGroupBox("Veterinarian Information")
        vet_layout = QFormLayout()
        
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Enter your full name")
        vet_layout.addRow("Full Name:", self.full_name_edit)
        
        self.specialization_edit = QLineEdit()
        self.specialization_edit.setPlaceholderText("Enter your specialization")
        vet_layout.addRow("Specialization:", self.specialization_edit)
        
        self.license_edit = QLineEdit()
        self.license_edit.setPlaceholderText("Enter your license number")
        vet_layout.addRow("License Number:", self.license_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Enter your phone number")
        vet_layout.addRow("Phone:", self.phone_edit)
        
        self.bio_edit = QLineEdit()
        self.bio_edit.setPlaceholderText("Enter a brief bio")
        vet_layout.addRow("Bio:", self.bio_edit)
        
        vet_group.setLayout(vet_layout)
        layout.addWidget(vet_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.register_button = QPushButton("Register")
        self.register_button.setDefault(True)
        self.register_button.clicked.connect(self.try_register)
        button_layout.addWidget(self.register_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Set focus to username field
        self.username_edit.setFocus()
    
    def try_register(self):
        """Try to register a new user and veterinarian"""
        # Get user information
        username = self.username_edit.text().strip().lower()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        
        # Get veterinarian information
        full_name = self.full_name_edit.text().strip()
        specialization = self.specialization_edit.text().strip()
        license_number = self.license_edit.text().strip()
        phone = self.phone_edit.text().strip()
        bio = self.bio_edit.text().strip()
        
        # Validate input
        if not username or not email or not password or not confirm_password or not first_name or not last_name:
            QMessageBox.warning(
                self,
                "Registration Failed",
                "Please fill in all user information fields."
            )
            return
        
        if not full_name or not specialization or not license_number or not phone:
            QMessageBox.warning(
                self,
                "Registration Failed",
                "Please fill in all veterinarian information fields."
            )
            return
        
        if password != confirm_password:
            QMessageBox.warning(
                self,
                "Registration Failed",
                "Passwords do not match."
            )
            return
        
        # Check if username already exists
        if self.user_data_access.get_by_username(username):
            QMessageBox.warning(
                self,
                "Registration Failed",
                "Username already exists."
            )
            return
        
        # Check if email already exists
        if self.user_data_access.get_by_email(email):
            QMessageBox.warning(
                self,
                "Registration Failed",
                "Email already exists."
            )
            return
        
        # Check if license number already exists
        if license_number and self.vet_data_access.get_by_license_number(license_number):
            QMessageBox.warning(
                self,
                "Registration Failed",
                "License number already exists."
            )
            return
        
        # Create user
        success, result = self.user_data_access.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        if not success:
            QMessageBox.warning(
                self,
                "Registration Failed",
                f"Failed to create user: {result}"
            )
            return
        
        # Get the user ID
        user_id = result
        self.user_id = user_id
        
        # Create veterinarian
        success, result = self.vet_data_access.create(
            user_id=user_id,
            full_name=full_name,
            specialization=specialization,
            license_number=license_number,
            phone=phone,
            bio=bio
        )
        
        if not success:
            QMessageBox.warning(
                self,
                "Registration Failed",
                f"Failed to create veterinarian profile: {result}"
            )
            return
        
        # Registration successful
        QMessageBox.information(
            self,
            "Registration Successful",
            "Your account has been created successfully.\n\n"
            "You can now log in with your username and password."
        )
        
        self.accept()
    
    def get_user_id(self):
        """Get the ID of the created user"""
        return self.user_id