"""
Login dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QIcon

from models.data_access import UserDataAccess, VeterinarianDataAccess
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
