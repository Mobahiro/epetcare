"""
Registration dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox,
    QComboBox, QTextEdit, QScrollArea, QWidget, QTabWidget,
    QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QFont, QIcon, QRegularExpressionValidator

from models.data_access import UserDataAccess, VeterinarianDataAccess


class RegisterDialog(QDialog):
    """Registration dialog for new veterinarians"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data_access = UserDataAccess()
        self.vet_data_access = VeterinarianDataAccess()
        self.user_id = None
        self.vet_id = None
        
        self.setWindowTitle("ePetCare Vet Desktop - Registration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("ePetCare Vet Desktop")
        header_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        subtitle_label = QLabel("Veterinarian Registration")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Tab widget for multi-step registration
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabBarAutoHide(False)
        
        # Account Information Tab
        account_tab = QWidget()
        account_layout = QVBoxLayout(account_tab)
        
        account_group = QGroupBox("Account Information")
        account_form = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter a username (min 4 characters)")
        account_form.addRow("Username*:", self.username_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email address")
        account_form.addRow("Email*:", self.email_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter a password (min 8 characters)")
        self.password_edit.setEchoMode(QLineEdit.Password)
        account_form.addRow("Password*:", self.password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("Confirm your password")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        account_form.addRow("Confirm Password*:", self.confirm_password_edit)
        
        account_group.setLayout(account_form)
        account_layout.addWidget(account_group)
        
        # Personal Information Group
        personal_group = QGroupBox("Personal Information")
        personal_form = QFormLayout()
        
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Enter your first name")
        personal_form.addRow("First Name*:", self.first_name_edit)
        
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Enter your last name")
        personal_form.addRow("Last Name*:", self.last_name_edit)
        
        personal_group.setLayout(personal_form)
        account_layout.addWidget(personal_group)
        
        account_layout.addStretch()
        
        # Navigation buttons for account tab
        account_nav_layout = QHBoxLayout()
        account_nav_layout.addStretch()
        
        self.account_next_button = QPushButton("Next")
        self.account_next_button.clicked.connect(self.validate_account_info)
        account_nav_layout.addWidget(self.account_next_button)
        
        account_layout.addLayout(account_nav_layout)
        
        # Professional Information Tab
        professional_tab = QWidget()
        professional_layout = QVBoxLayout(professional_tab)
        
        professional_group = QGroupBox("Professional Information")
        professional_form = QFormLayout()
        
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Enter your full professional name")
        professional_form.addRow("Full Name*:", self.full_name_edit)
        
        self.specialization_edit = QComboBox()
        self.specialization_edit.addItem("General Practice")
        self.specialization_edit.addItem("Surgery")
        self.specialization_edit.addItem("Dermatology")
        self.specialization_edit.addItem("Cardiology")
        self.specialization_edit.addItem("Neurology")
        self.specialization_edit.addItem("Oncology")
        self.specialization_edit.addItem("Ophthalmology")
        self.specialization_edit.addItem("Dentistry")
        self.specialization_edit.addItem("Other")
        professional_form.addRow("Specialization*:", self.specialization_edit)
        
        self.license_number_edit = QLineEdit()
        self.license_number_edit.setPlaceholderText("Enter your license number")
        professional_form.addRow("License Number*:", self.license_number_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Enter your phone number")
        # Set validator for phone number
        phone_regex = QRegularExpression("^[0-9\\+\\-\\(\\)\\s]{6,20}$")
        self.phone_edit.setValidator(QRegularExpressionValidator(phone_regex))
        professional_form.addRow("Phone*:", self.phone_edit)
        
        self.bio_edit = QTextEdit()
        self.bio_edit.setPlaceholderText("Enter a brief professional bio")
        self.bio_edit.setMaximumHeight(100)
        professional_form.addRow("Bio:", self.bio_edit)
        
        professional_group.setLayout(professional_form)
        professional_layout.addWidget(professional_group)
        
        professional_layout.addStretch()
        
        # Navigation buttons for professional tab
        professional_nav_layout = QHBoxLayout()
        
        self.professional_back_button = QPushButton("Back")
        self.professional_back_button.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        professional_nav_layout.addWidget(self.professional_back_button)
        
        professional_nav_layout.addStretch()
        
        self.professional_next_button = QPushButton("Next")
        self.professional_next_button.clicked.connect(self.validate_professional_info)
        professional_nav_layout.addWidget(self.professional_next_button)
        
        professional_layout.addLayout(professional_nav_layout)
        
        # Review Tab
        review_tab = QWidget()
        review_layout = QVBoxLayout(review_tab)
        
        review_label = QLabel("Please review your information before submitting")
        review_label.setFont(QFont("Arial", 12))
        review_layout.addWidget(review_label)
        
        # Scroll area for review information
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Account review
        account_review_group = QGroupBox("Account Information")
        account_review_form = QFormLayout()
        
        self.username_review = QLabel()
        account_review_form.addRow("Username:", self.username_review)
        
        self.email_review = QLabel()
        account_review_form.addRow("Email:", self.email_review)
        
        account_review_group.setLayout(account_review_form)
        scroll_layout.addWidget(account_review_group)
        
        # Personal review
        personal_review_group = QGroupBox("Personal Information")
        personal_review_form = QFormLayout()
        
        self.name_review = QLabel()
        personal_review_form.addRow("Name:", self.name_review)
        
        personal_review_group.setLayout(personal_review_form)
        scroll_layout.addWidget(personal_review_group)
        
        # Professional review
        professional_review_group = QGroupBox("Professional Information")
        professional_review_form = QFormLayout()
        
        self.full_name_review = QLabel()
        professional_review_form.addRow("Full Name:", self.full_name_review)
        
        self.specialization_review = QLabel()
        professional_review_form.addRow("Specialization:", self.specialization_review)
        
        self.license_review = QLabel()
        professional_review_form.addRow("License Number:", self.license_review)
        
        self.phone_review = QLabel()
        professional_review_form.addRow("Phone:", self.phone_review)
        
        self.bio_review = QLabel()
        self.bio_review.setWordWrap(True)
        professional_review_form.addRow("Bio:", self.bio_review)
        
        professional_review_group.setLayout(professional_review_form)
        scroll_layout.addWidget(professional_review_group)
        
        # Terms and conditions
        self.terms_check = QCheckBox("I agree to the terms and conditions")
        scroll_layout.addWidget(self.terms_check)
        
        scroll_area.setWidget(scroll_widget)
        review_layout.addWidget(scroll_area)
        
        # Navigation buttons for review tab
        review_nav_layout = QHBoxLayout()
        
        self.review_back_button = QPushButton("Back")
        self.review_back_button.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        review_nav_layout.addWidget(self.review_back_button)
        
        review_nav_layout.addStretch()
        
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register)
        self.register_button.setEnabled(False)
        review_nav_layout.addWidget(self.register_button)
        
        review_layout.addLayout(review_nav_layout)
        
        # Connect terms checkbox to enable/disable register button
        self.terms_check.stateChanged.connect(self.update_register_button)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(account_tab, "Account")
        self.tab_widget.addTab(professional_tab, "Professional")
        self.tab_widget.addTab(review_tab, "Review")
        
        # Disable tabs initially
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(2, False)
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def validate_account_info(self):
        """Validate account information and move to next tab"""
        # Check required fields
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        
        if not username or not email or not password or not confirm_password or not first_name or not last_name:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please fill in all required fields."
            )
            return
        
        # Validate username length
        if len(username) < 4:
            QMessageBox.warning(
                self,
                "Invalid Username",
                "Username must be at least 4 characters long."
            )
            return
        
        # Check if username already exists
        if self.user_data_access.get_by_username(username):
            QMessageBox.warning(
                self,
                "Username Taken",
                "This username is already taken. Please choose another one."
            )
            return
        
        # Validate email format
        if '@' not in email or '.' not in email:
            QMessageBox.warning(
                self,
                "Invalid Email",
                "Please enter a valid email address."
            )
            return
        
        # Check if email already exists
        if self.user_data_access.get_by_email(email):
            QMessageBox.warning(
                self,
                "Email Already Registered",
                "This email is already registered. Please use another email address."
            )
            return
        
        # Validate password length
        if len(password) < 8:
            QMessageBox.warning(
                self,
                "Invalid Password",
                "Password must be at least 8 characters long."
            )
            return
        
        # Check if passwords match
        if password != confirm_password:
            QMessageBox.warning(
                self,
                "Passwords Don't Match",
                "The passwords you entered don't match."
            )
            return
        
        # Fill in professional tab with personal info
        self.full_name_edit.setText(f"{first_name} {last_name}")
        
        # Enable next tab and switch to it
        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setCurrentIndex(1)
    
    def validate_professional_info(self):
        """Validate professional information and move to review tab"""
        # Check required fields
        full_name = self.full_name_edit.text().strip()
        specialization = self.specialization_edit.currentText()
        license_number = self.license_number_edit.text().strip()
        phone = self.phone_edit.text().strip()
        
        if not full_name or not specialization or not license_number or not phone:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please fill in all required fields."
            )
            return
        
        # Check if license number already exists
        if license_number and self.vet_data_access.get_by_license_number(license_number):
            QMessageBox.warning(
                self,
                "License Number Already Registered",
                "This license number is already registered. Please check your information."
            )
            return
        
        # Update review tab
        self.username_review.setText(self.username_edit.text().strip())
        self.email_review.setText(self.email_edit.text().strip())
        self.name_review.setText(f"{self.first_name_edit.text().strip()} {self.last_name_edit.text().strip()}")
        self.full_name_review.setText(full_name)
        self.specialization_review.setText(specialization)
        self.license_review.setText(license_number)
        self.phone_review.setText(phone)
        self.bio_review.setText(self.bio_edit.toPlainText())
        
        # Enable review tab and switch to it
        self.tab_widget.setTabEnabled(2, True)
        self.tab_widget.setCurrentIndex(2)
    
    def update_register_button(self):
        """Update the state of the register button based on terms checkbox"""
        self.register_button.setEnabled(self.terms_check.isChecked())
    
    def register(self):
        """Register the new veterinarian"""
        # Get user information
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        
        # Get veterinarian information
        full_name = self.full_name_edit.text().strip()
        specialization = self.specialization_edit.currentText()
        license_number = self.license_number_edit.text().strip()
        phone = self.phone_edit.text().strip()
        bio = self.bio_edit.toPlainText()
        
        # Create user
        success, result = self.user_data_access.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        if not success:
            QMessageBox.critical(
                self,
                "Registration Failed",
                f"Failed to create user account: {result}"
            )
            return
        
        # Get the new user ID
        self.user_id = result
        
        # Create veterinarian
        success, result = self.vet_data_access.create(
            user_id=self.user_id,
            full_name=full_name,
            specialization=specialization,
            license_number=license_number,
            phone=phone,
            bio=bio
        )
        
        if not success:
            QMessageBox.critical(
                self,
                "Registration Failed",
                f"Failed to create veterinarian profile: {result}"
            )
            return
        
        # Get the new veterinarian ID
        self.vet_id = result
        
        # Show success message
        QMessageBox.information(
            self,
            "Registration Successful",
            "Your registration was successful. You can now log in with your new account."
        )
        
        # Close the dialog
        self.accept()
    
    def get_user_id(self):
        """Get the ID of the newly created user"""
        return self.user_id
    
    def get_vet_id(self):
        """Get the ID of the newly created veterinarian"""
        return self.vet_id
