"""
Superadmin Dashboard for managing users and approvals
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QHeaderView,
    QLineEdit, QComboBox, QGroupBox, QDialog,
    QFormLayout, QDialogButtonBox, QTextEdit, QScrollArea,
    QFrame, QSplitter, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import logging
import secrets
import string

logger = logging.getLogger('epetcare')

try:
    from models.data_access import UserDataAccess, VeterinarianDataAccess, OwnerDataAccess
    from utils.pg_db import get_connection
except ImportError as e:
    logger.error(f"Import error in superadmin_dashboard.py: {e}")
    # Fallback
    from models.data_access import UserDataAccess, VeterinarianDataAccess, OwnerDataAccess
    from utils.database import get_connection


class EditUserDialog(QDialog):
    """Dialog for editing user information"""
    def __init__(self, user_id, user_data, user_type, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.user_type = user_type
        self.user_data = user_data
        self.setWindowTitle(f"Edit {user_type.title()}")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.username_edit = QLineEdit(str(self.user_data.get('username', '')))
        self.email_edit = QLineEdit(str(self.user_data.get('email', '')))
        self.full_name_edit = QLineEdit(str(self.user_data.get('full_name', '')))
        
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Full Name:", self.full_name_edit)
        
        if self.user_type == 'owner':
            self.phone_edit = QLineEdit(str(self.user_data.get('phone', '') or ''))
            self.address_edit = QTextEdit()
            self.address_edit.setPlainText(str(self.user_data.get('address', '') or ''))
            self.address_edit.setMaximumHeight(80)
            layout.addRow("Phone:", self.phone_edit)
            layout.addRow("Address:", self.address_edit)
        elif self.user_type == 'vet':
            self.specialization_edit = QLineEdit(str(self.user_data.get('specialization', '') or ''))
            self.license_edit = QLineEdit(str(self.user_data.get('license_number', '') or ''))
            layout.addRow("Specialization:", self.specialization_edit)
            layout.addRow("License Number:", self.license_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_data(self):
        data = {
            'username': self.username_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'full_name': self.full_name_edit.text().strip(),
        }
        if self.user_type == 'owner':
            data['phone'] = self.phone_edit.text().strip()
            data['address'] = self.address_edit.toPlainText().strip()
        elif self.user_type == 'vet':
            data['specialization'] = self.specialization_edit.text().strip()
            data['license_number'] = self.license_edit.text().strip()
        return data
    
    def accept(self):
        """Save the edited user data"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            data = self.get_data()
            
            # Update auth_user
            cursor.execute("""
                UPDATE auth_user SET username = %s, email = %s WHERE id = %s
            """, (data['username'], data['email'], self.user_id))
            
            if self.user_type == 'vet':
                cursor.execute("""
                    UPDATE vet_veterinarian 
                    SET full_name = %s, specialization = %s, license_number = %s
                    WHERE user_id = %s
                """, (data['full_name'], data.get('specialization', ''), data.get('license_number', ''), self.user_id))
            else:
                cursor.execute("""
                    UPDATE clinic_owner 
                    SET full_name = %s, phone = %s, address = %s
                    WHERE user_id = %s
                """, (data['full_name'], data.get('phone', ''), data.get('address', ''), self.user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            super().accept()
        except Exception as e:
            self._show_error(f"Failed to save: {str(e)}")
    
    def _show_error(self, message):
        """Show error with visible button"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Error")
        dialog.setFixedSize(320, 120)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        label = QLabel(f"❌ {message}")
        label.setStyleSheet("color: #ef4444; font-size: 13px;")
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        btn = QPushButton("OK")
        btn.setFixedSize(80, 32)
        btn.setStyleSheet("background: #ef4444; color: white; border: none; border-radius: 6px; font-weight: bold;")
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        dialog.exec()


class ResetPasswordDialog(QDialog):
    """Dialog for resetting user password"""
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle(f"Reset Password")
        self.setMinimumWidth(350)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel(f"Reset password for user ID: <b>{self.user_id}</b>")
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("New Password:", self.new_password)
        form_layout.addRow("Confirm Password:", self.confirm_password)
        layout.addLayout(form_layout)
        
        # Generate random password button
        generate_btn = QPushButton("Generate Random Password")
        generate_btn.clicked.connect(self.generate_password)
        layout.addWidget(generate_btn)
        
        self.generated_label = QLabel("")
        self.generated_label.setStyleSheet("color: #007bff; font-family: monospace;")
        layout.addWidget(self.generated_label)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(secrets.choice(chars) for _ in range(12))
        self.new_password.setText(password)
        self.confirm_password.setText(password)
        self.generated_label.setText(f"Generated: {password}")
    
    def validate_and_accept(self):
        if self.new_password.text() != self.confirm_password.text():
            self._show_error("Passwords do not match!")
            return
        if len(self.new_password.text()) < 8:
            self._show_error("Password must be at least 8 characters!")
            return
        
        # Save the new password using Django-compatible PBKDF2 hashing
        try:
            from utils.password_hasher import make_password
            
            hashed = make_password(self.new_password.text())
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE auth_user SET password = %s WHERE id = %s", (hashed, self.user_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            self._show_success("Password has been reset successfully!")
            self.accept()
        except Exception as e:
            self._show_error(f"Failed to reset password: {str(e)}")
    
    def _show_error(self, message):
        """Show error with visible button"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Error")
        dialog.setFixedSize(320, 120)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        label = QLabel(f"❌ {message}")
        label.setStyleSheet("color: #ef4444; font-size: 13px;")
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        btn = QPushButton("OK")
        btn.setFixedSize(80, 32)
        btn.setStyleSheet("background: #ef4444; color: white; border: none; border-radius: 6px; font-weight: bold;")
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def _show_success(self, message):
        """Show success with visible button"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Success")
        dialog.setFixedSize(320, 120)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        label = QLabel(f"✅ {message}")
        label.setStyleSheet("color: #10b981; font-size: 13px;")
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        btn = QPushButton("OK")
        btn.setFixedSize(80, 32)
        btn.setStyleSheet("background: #10b981; color: white; border: none; border-radius: 6px; font-weight: bold;")
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def get_password(self):
        return self.new_password.text()


class AddSuperadminDialog(QDialog):
    """Dialog for adding a new superadmin"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Superadmin")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("👑 Create Superadmin Account")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b; margin-bottom: 10px;")
        layout.addRow(title)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username (e.g., admin)")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email address")
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Full name")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password (min 8 chars)")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("Confirm password")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        
        input_style = """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """
        self.username_edit.setStyleSheet(input_style)
        self.email_edit.setStyleSheet(input_style)
        self.full_name_edit.setStyleSheet(input_style)
        self.password_edit.setStyleSheet(input_style)
        self.confirm_password_edit.setStyleSheet(input_style)
        
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Full Name:", self.full_name_edit)
        layout.addRow("Password:", self.password_edit)
        layout.addRow("Confirm:", self.confirm_password_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #64748b;
                border: 1px solid #e2e8f0;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create Superadmin")
        create_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        create_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(create_btn)
        layout.addRow(btn_layout)
    
    def accept(self):
        """Validate and create the superadmin"""
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        full_name = self.full_name_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_password_edit.text()
        
        # Validation
        if not all([username, email, full_name, password]):
            self._show_error("All fields are required")
            return
        
        if len(password) < 8:
            self._show_error("Password must be at least 8 characters")
            return
        
        if password != confirm:
            self._show_error("Passwords do not match")
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute("SELECT id FROM auth_user WHERE username = %s", (username,))
            if cursor.fetchone():
                self._show_error("Username already exists")
                cursor.close()
                conn.close()
                return
            
            # Hash password using Django-compatible PBKDF2
            from utils.password_hasher import make_password
            password_hash = make_password(password)
            
            # Create auth_user
            cursor.execute("""
                INSERT INTO auth_user (username, email, password, first_name, last_name, 
                    is_superuser, is_staff, is_active, date_joined)
                VALUES (%s, %s, %s, %s, '', TRUE, TRUE, TRUE, NOW())
                RETURNING id
            """, (username, email, password_hash, full_name))
            user_id = cursor.fetchone()['id']
            
            # Create superadmin profile
            cursor.execute("""
                INSERT INTO vet_superadmin (user_id, full_name, email, is_active, created_at)
                VALUES (%s, %s, %s, TRUE, NOW())
            """, (user_id, full_name, email))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            super().accept()
            
        except Exception as e:
            logger.error(f"Error creating superadmin: {e}")
            self._show_error(f"Failed to create superadmin: {str(e)}")
    
    def _show_error(self, message):
        """Show error dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Error")
        dialog.setFixedSize(320, 120)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        label = QLabel(f"❌ {message}")
        label.setStyleSheet("color: #ef4444; font-size: 13px;")
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        btn = QPushButton("OK")
        btn.setFixedSize(80, 32)
        btn.setStyleSheet("background: #ef4444; color: white; border: none; border-radius: 6px; font-weight: bold;")
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        dialog.exec()


class EditSuperadminDialog(QDialog):
    """Dialog for editing superadmin information"""
    def __init__(self, superadmin_id, superadmin_data, parent=None):
        super().__init__(parent)
        self.superadmin_id = superadmin_id
        self.superadmin_data = superadmin_data
        self.setWindowTitle("Edit Superadmin")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.username_edit = QLineEdit(str(self.superadmin_data.get('username', '')))
        self.email_edit = QLineEdit(str(self.superadmin_data.get('email', '')))
        self.full_name_edit = QLineEdit(str(self.superadmin_data.get('full_name', '')))
        
        input_style = """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """
        self.username_edit.setStyleSheet(input_style)
        self.email_edit.setStyleSheet(input_style)
        self.full_name_edit.setStyleSheet(input_style)
        
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Full Name:", self.full_name_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #64748b;
                border: 1px solid #e2e8f0;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #4f46e5;
            }
        """)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addRow(btn_layout)
    
    def accept(self):
        """Save the edited superadmin data"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            username = self.username_edit.text().strip()
            email = self.email_edit.text().strip()
            full_name = self.full_name_edit.text().strip()
            
            user_id = self.superadmin_data.get('user_id')
            
            # Update auth_user
            cursor.execute("""
                UPDATE auth_user SET username = %s, email = %s WHERE id = %s
            """, (username, email, user_id))
            
            # Update vet_superadmin
            cursor.execute("""
                UPDATE vet_superadmin SET full_name = %s, email = %s WHERE id = %s
            """, (full_name, email, self.superadmin_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            super().accept()
            
        except Exception as e:
            self._show_error(f"Failed to save: {str(e)}")
    
    def _show_error(self, message):
        """Show error dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Error")
        dialog.setFixedSize(320, 120)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        label = QLabel(f"❌ {message}")
        label.setStyleSheet("color: #ef4444; font-size: 13px;")
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
        btn = QPushButton("OK")
        btn.setFixedSize(80, 32)
        btn.setStyleSheet("background: #ef4444; color: white; border: none; border-radius: 6px; font-weight: bold;")
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        dialog.exec()


class SuperadminDashboard(QWidget):
    """Superadmin Dashboard for managing all users - Modern UI"""
    
    logout_requested = Signal()
    
    # Modern color scheme
    COLORS = {
        'primary': '#6366f1',      # Indigo
        'primary_dark': '#4f46e5',
        'success': '#10b981',      # Emerald
        'warning': '#f59e0b',      # Amber
        'danger': '#ef4444',       # Red
        'bg': '#f8fafc',           # Slate 50
        'surface': '#ffffff',
        'border': '#e2e8f0',       # Slate 200
        'text': '#1e293b',         # Slate 800
        'text_secondary': '#64748b', # Slate 500
        'taguig': '#06b6d4',       # Cyan - Taguig branch
        'pasig': '#f97316',        # Orange - Pasig branch
        'makati': '#8b5cf6',       # Violet - Makati branch
    }
    
    def __init__(self, superadmin_user=None, parent=None):
        super().__init__(parent)
        self.superadmin_user = superadmin_user
        self.user_data_access = UserDataAccess()
        self.vet_data_access = VeterinarianDataAccess()
        self.owner_data_access = OwnerDataAccess()
        
        # Initialize data lists
        self.vet_data = []
        self.owner_data = []
        self.pet_data = []
        self.superadmin_data = []
        
        self.setup_ui()
        self.load_data()
    
    def show_confirm_dialog(self, title, message, confirm_text="Yes", cancel_text="Cancel", is_danger=False):
        """Show a custom confirmation dialog with visible buttons"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(380, 180)
        dialog.setStyleSheet(f"""
            QDialog {{
                background: {self.COLORS['surface']};
            }}
            QLabel {{
                color: {self.COLORS['text']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("font-size: 13px;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['bg']};
                color: {self.COLORS['text']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {self.COLORS['border']};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setFixedSize(100, 36)
        confirm_btn.setCursor(Qt.PointingHandCursor)
        btn_color = self.COLORS['danger'] if is_danger else self.COLORS['success']
        btn_hover = '#dc2626' if is_danger else '#059669'
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_color};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {btn_hover};
            }}
        """)
        confirm_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(confirm_btn)
        
        layout.addLayout(btn_layout)
        
        return dialog.exec() == QDialog.Accepted
    
    def show_info_dialog(self, title, message):
        """Show an info dialog with visible OK button"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(350, 150)
        dialog.setStyleSheet(f"""
            QDialog {{
                background: {self.COLORS['surface']};
            }}
            QLabel {{
                color: {self.COLORS['text']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Message with checkmark
        msg_label = QLabel(f"✅ {message}")
        msg_label.setStyleSheet(f"font-size: 13px; color: {self.COLORS['success']};")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # OK Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(100, 36)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {self.COLORS['primary_dark']};
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def show_error_dialog(self, title, message):
        """Show an error dialog with visible OK button"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(380, 150)
        dialog.setStyleSheet(f"""
            QDialog {{
                background: {self.COLORS['surface']};
            }}
            QLabel {{
                color: {self.COLORS['text']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Message with error icon
        msg_label = QLabel(f"❌ {message}")
        msg_label.setStyleSheet(f"font-size: 13px; color: {self.COLORS['danger']};")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # OK Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(100, 36)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['danger']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #dc2626;
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def setup_ui(self):
        """Set up the modern user interface"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.COLORS['bg']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {self.COLORS['text']};
            }}
            QLineEdit {{
                padding: 10px 14px;
                border: 1px solid {self.COLORS['border']};
                border-radius: 8px;
                background: {self.COLORS['surface']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {self.COLORS['primary']};
            }}
            QComboBox {{
                padding: 8px 12px;
                border: 1px solid {self.COLORS['border']};
                border-radius: 8px;
                background: {self.COLORS['surface']};
                font-size: 13px;
            }}
            QTableWidget {{
                background-color: {self.COLORS['surface']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 12px;
                gridline-color: {self.COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {self.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {self.COLORS['bg']};
                color: {self.COLORS['text_secondary']};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {self.COLORS['border']};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                padding: 12px 24px;
                margin-right: 4px;
                border: none;
                border-radius: 8px 8px 0 0;
                background: transparent;
                color: {self.COLORS['text_secondary']};
                font-weight: 500;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background: {self.COLORS['surface']};
                color: {self.COLORS['primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background: rgba(99, 102, 241, 0.1);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header Bar
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            QFrame {{
                background: {self.COLORS['surface']};
                border-bottom: 1px solid {self.COLORS['border']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        # Logo and title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        logo_label = QLabel("🏥")
        logo_label.setStyleSheet("font-size: 28px;")
        title_layout.addWidget(logo_label)
        
        title_text = QVBoxLayout()
        title_text.setSpacing(0)
        main_title = QLabel("ePetCare Admin")
        main_title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {self.COLORS['text']};")
        subtitle = QLabel("Superadmin Dashboard")
        subtitle.setStyleSheet(f"font-size: 12px; color: {self.COLORS['text_secondary']};")
        title_text.addWidget(main_title)
        title_text.addWidget(subtitle)
        title_layout.addLayout(title_text)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Logout button
        logout_btn = QPushButton("← Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.COLORS['text_secondary']};
                padding: 10px 20px;
                border: 1px solid {self.COLORS['border']};
                border-radius: 8px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {self.COLORS['danger']};
                color: white;
                border-color: {self.COLORS['danger']};
            }}
        """)
        logout_btn.clicked.connect(self.logout_requested.emit)
        header_layout.addWidget(logout_btn)
        
        layout.addWidget(header)
        
        # Main content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(24)
        
        # Statistics Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        # Branch stats
        self.branch_stats = {
            'taguig': self.create_stat_card("📍 Taguig Branch", "0 Vets", self.COLORS['taguig']),
            'pasig': self.create_stat_card("📍 Pasig Branch", "0 Vets", self.COLORS['pasig']),
            'makati': self.create_stat_card("📍 Makati Branch", "0 Vets", self.COLORS['makati']),
        }
        
        for card in self.branch_stats.values():
            stats_layout.addWidget(card)
        
        # User stats
        self.total_vets_card = self.create_stat_card("🩺 Total Vets", "0", self.COLORS['primary'])
        self.pending_vets_card = self.create_stat_card("⏳ Pending", "0", self.COLORS['warning'])
        self.total_owners_card = self.create_stat_card("🐾 Pet Owners", "0", self.COLORS['success'])
        
        stats_layout.addWidget(self.total_vets_card)
        stats_layout.addWidget(self.pending_vets_card)
        stats_layout.addWidget(self.total_owners_card)
        
        content_layout.addLayout(stats_layout)
        
        # Tabs container with shadow
        tabs_container = QFrame()
        tabs_container.setStyleSheet(f"""
            QFrame {{
                background: {self.COLORS['surface']};
                border-radius: 16px;
                border: 1px solid {self.COLORS['border']};
            }}
        """)
        tabs_layout = QVBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        # Veterinarians tab
        self.vets_widget = self.create_vets_table()
        self.tabs.addTab(self.vets_widget, "🩺 Veterinarians")
        
        # Pet Owners tab
        self.owners_widget = self.create_owners_table()
        self.tabs.addTab(self.owners_widget, "🐾 Pet Owners")
        
        # Pets tab
        self.pets_widget = self.create_pets_table()
        self.tabs.addTab(self.pets_widget, "🐕 All Pets")
        
        # Superadmins tab
        self.superadmins_widget = self.create_superadmins_table()
        self.tabs.addTab(self.superadmins_widget, "👑 Superadmins")
        
        # Reports tab
        self.reports_widget = self.create_reports_tab()
        self.tabs.addTab(self.reports_widget, "📊 Reports")
        
        tabs_layout.addWidget(self.tabs)
        content_layout.addWidget(tabs_container)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh Data")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['primary']};
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {self.COLORS['primary_dark']};
            }}
        """)
        refresh_btn.clicked.connect(self.load_data)
        refresh_layout.addWidget(refresh_btn)
        
        content_layout.addLayout(refresh_layout)
        
        layout.addWidget(content)
    
    def create_stat_card(self, title, value, color):
        """Create a modern stat card"""
        card = QFrame()
        card.setFixedHeight(90)
        card.setStyleSheet(f"""
            QFrame {{
                background: {self.COLORS['surface']};
                border-radius: 12px;
                border: 1px solid {self.COLORS['border']};
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 12px;
            color: {self.COLORS['text_secondary']};
            font-weight: 500;
        """)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {color};
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        
        return card
    
    def update_stat_card(self, card, value):
        """Update the value in a stat card"""
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(str(value))
    
    def create_report_stat_card(self, title, value, icon, color):
        """Create a report stat card with icon"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {self.COLORS['surface']};
                border-radius: 12px;
                border: 1px solid {self.COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 28px;
            background: {color}20;
            padding: 8px;
            border-radius: 8px;
        """)
        layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 12px;
            color: {self.COLORS['text_secondary']};
        """)
        
        value_label = QLabel(value)
        value_label.setObjectName(f"stat_{title.lower().replace(' ', '_')}")
        value_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {self.COLORS['text']};
        """)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return card
    
    def create_vets_table(self):
        """Create the veterinarians table with branch info"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Search and filter bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        
        self.vet_search = QLineEdit()
        self.vet_search.setPlaceholderText("🔍 Search by username, email, or name...")
        self.vet_search.textChanged.connect(self.filter_vets)
        search_layout.addWidget(self.vet_search, 3)
        
        # Status filter
        self.vet_status_filter = QComboBox()
        self.vet_status_filter.addItems(["All Status", "Approved", "Pending", "Rejected"])
        self.vet_status_filter.currentTextChanged.connect(self.filter_vets_by_status)
        search_layout.addWidget(self.vet_status_filter, 1)
        
        # Branch filter
        self.vet_branch_filter = QComboBox()
        self.vet_branch_filter.addItems(["All Branches", "Taguig", "Pasig", "Makati"])
        self.vet_branch_filter.currentTextChanged.connect(self.filter_vets_by_branch)
        search_layout.addWidget(self.vet_branch_filter, 1)
        
        layout.addLayout(search_layout)
        
        # Table with Branch column
        self.vets_table = QTableWidget()
        self.vets_table.setColumnCount(10)
        self.vets_table.setHorizontalHeaderLabels([
            "ID", "Username", "Email", "Full Name", "Branch",
            "Specialization", "License #", "Access Code", "Status", "Actions"
        ])
        
        # Set column widths
        header = self.vets_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        # Set minimum width for Actions column
        self.vets_table.setColumnWidth(9, 280)
        
        self.vets_table.setAlternatingRowColors(True)
        self.vets_table.verticalHeader().setVisible(False)
        self.vets_table.setShowGrid(False)
        # Set row height for better button visibility
        self.vets_table.verticalHeader().setDefaultSectionSize(45)
        
        layout.addWidget(self.vets_table)
        return widget
    
    def create_owners_table(self):
        """Create the pet owners table with branch info"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        
        self.owner_search = QLineEdit()
        self.owner_search.setPlaceholderText("🔍 Search by username, email, or name...")
        self.owner_search.textChanged.connect(self.filter_owners)
        search_layout.addWidget(self.owner_search, 3)
        
        # Branch filter
        self.owner_branch_filter = QComboBox()
        self.owner_branch_filter.addItems(["All Branches", "Taguig", "Pasig", "Makati"])
        self.owner_branch_filter.currentTextChanged.connect(self.filter_owners_by_branch)
        search_layout.addWidget(self.owner_branch_filter, 1)
        
        layout.addLayout(search_layout)
        
        # Table with Branch column
        self.owners_table = QTableWidget()
        self.owners_table.setColumnCount(9)
        self.owners_table.setHorizontalHeaderLabels([
            "ID", "Username", "Email", "Full Name", "Branch",
            "Phone", "Address", "Status", "Actions"
        ])
        
        # Set column widths
        header = self.owners_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        # Set minimum width for Actions column
        self.owners_table.setColumnWidth(8, 250)
        
        self.owners_table.setAlternatingRowColors(True)
        self.owners_table.verticalHeader().setVisible(False)
        self.owners_table.setShowGrid(False)
        # Set row height for better button visibility
        self.owners_table.verticalHeader().setDefaultSectionSize(45)
        
        layout.addWidget(self.owners_table)
        return widget
    
    def create_pets_table(self):
        """Create the pets table with modern styling"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.pet_search = QLineEdit()
        self.pet_search.setPlaceholderText("🔍 Search by pet name, species, or owner...")
        self.pet_search.textChanged.connect(self.filter_pets)
        search_layout.addWidget(self.pet_search)
        layout.addLayout(search_layout)
        
        # Table
        self.pets_table = QTableWidget()
        self.pets_table.setColumnCount(8)
        self.pets_table.setHorizontalHeaderLabels([
            "ID", "Name", "Species", "Breed", "Sex", "Birth Date", "Owner", "Weight (kg)"
        ])
        
        header = self.pets_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        self.pets_table.setAlternatingRowColors(True)
        self.pets_table.verticalHeader().setVisible(False)
        self.pets_table.setShowGrid(False)
        
        layout.addWidget(self.pets_table)
        return widget
    
    def create_appointments_table(self):
        """Create the appointments table"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filter bar
        filter_layout = QHBoxLayout()
        
        status_label = QLabel("Status:")
        self.appt_status_filter = QComboBox()
        self.appt_status_filter.addItems(["All", "Scheduled", "Completed", "Cancelled"])
        self.appt_status_filter.currentTextChanged.connect(self.filter_appointments)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.appt_status_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Table
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(7)
        self.appointments_table.setHorizontalHeaderLabels([
            "ID", "Pet", "Owner", "Vet", "Date/Time", "Reason", "Status"
        ])
        
        header = self.appointments_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        self.appointments_table.setAlternatingRowColors(True)
        self.appointments_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                selection-background-color: #6f42c1;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        layout.addWidget(self.appointments_table)
        return widget
    
    def create_superadmins_table(self):
        """Create the superadmins management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        
        title = QLabel("👑 Superadmin Accounts")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.COLORS['text']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add superadmin button
        add_btn = QPushButton("➕ Add Superadmin")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['success']};
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: #059669;
            }}
        """)
        add_btn.clicked.connect(self.add_superadmin)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Info box
        info_box = QLabel("ℹ️ Superadmin accounts have full access to the system and are separate from veterinarian accounts.")
        info_box.setStyleSheet(f"""
            background: #eff6ff;
            color: #1e40af;
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
        """)
        info_box.setWordWrap(True)
        layout.addWidget(info_box)
        
        # Table
        self.superadmins_table = QTableWidget()
        self.superadmins_table.setColumnCount(6)
        self.superadmins_table.setHorizontalHeaderLabels([
            "ID", "Username", "Email", "Full Name", "Created", "Actions"
        ])
        
        # Set column widths
        self.superadmins_table.setColumnWidth(0, 50)
        self.superadmins_table.setColumnWidth(1, 150)
        self.superadmins_table.setColumnWidth(2, 200)
        self.superadmins_table.setColumnWidth(3, 200)
        self.superadmins_table.setColumnWidth(4, 150)
        self.superadmins_table.setColumnWidth(5, 200)
        
        header = self.superadmins_table.horizontalHeader()
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.superadmins_table.verticalHeader().setVisible(False)
        self.superadmins_table.setAlternatingRowColors(True)
        self.superadmins_table.setShowGrid(False)
        self.superadmins_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.superadmins_table.verticalHeader().setDefaultSectionSize(45)
        
        self.superadmins_table.setStyleSheet(f"""
            QTableWidget {{
                background: {self.COLORS['surface']};
                border: none;
                border-radius: 8px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background: {self.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background: {self.COLORS['bg']};
                color: {self.COLORS['text']};
                font-weight: 600;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.COLORS['primary']};
            }}
        """)
        
        layout.addWidget(self.superadmins_table)
        return widget
    
    def add_superadmin(self):
        """Show dialog to add a new superadmin"""
        dialog = AddSuperadminDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def create_reports_tab(self):
        """Create the reports tab with modern styling"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("📊 System Reports & Statistics")
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {self.COLORS['text']};")
        layout.addWidget(title)
        
        # Stats cards
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"QFrame {{ background: {self.COLORS['bg']}; border-radius: 12px; padding: 16px; }}")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(12)
        
        self.report_total_users = self.create_report_stat_card("Total Users", "0", "👥", self.COLORS['primary'])
        self.report_total_vets = self.create_report_stat_card("Total Vets", "0", "🩺", self.COLORS['success'])
        self.report_total_owners = self.create_report_stat_card("Total Owners", "0", "🐾", self.COLORS['makati'])
        self.report_total_pets = self.create_report_stat_card("Total Pets", "0", "🐕", self.COLORS['taguig'])
        
        stats_layout.addWidget(self.report_total_users)
        stats_layout.addWidget(self.report_total_vets)
        stats_layout.addWidget(self.report_total_owners)
        stats_layout.addWidget(self.report_total_pets)
        
        layout.addWidget(stats_frame)
        
        # Recent activity
        activity_label = QLabel("📋 Recent System Activity")
        activity_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self.COLORS['text']}; margin-top: 8px;")
        layout.addWidget(activity_label)
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Date", "Type", "User", "Description"])
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setShowGrid(False)
        
        layout.addWidget(self.activity_table)
        
        # Generate report button
        generate_btn = QPushButton("📥 Export Report (CSV)")
        generate_btn.setCursor(Qt.PointingHandCursor)
        generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLORS['makati']};
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #7c3aed;
            }}
        """)
        generate_btn.clicked.connect(self.export_report)
        layout.addWidget(generate_btn)
        
        return widget
    
    def load_data(self):
        """Load all users data"""
        try:
            conn = get_connection()
            if not conn:
                self.show_error_dialog("Error", "Failed to connect to database")
                return
            
            cursor = conn.cursor()
            
            # Load veterinarians with branch info
            cursor.execute("""
                SELECT 
                    v.id, u.username, u.email,
                    v.full_name, v.branch, v.specialization, v.license_number, v.access_code, v.approval_status,
                    u.id as user_id
                FROM vet_veterinarian v
                JOIN auth_user u ON v.user_id = u.id
                ORDER BY v.id DESC
            """)
            self.vet_data = cursor.fetchall()
            self.display_vets(self.vet_data)
            
            # Load pet owners with branch info
            cursor.execute("""
                SELECT 
                    o.id, u.username, u.email,
                    o.full_name, o.branch, o.phone, o.address, u.is_active,
                    u.id as user_id
                FROM clinic_owner o
                JOIN auth_user u ON o.user_id = u.id
                ORDER BY o.id DESC
            """)
            self.owner_data = cursor.fetchall()
            self.display_owners(self.owner_data)
            
            # Load pets
            cursor.execute("""
                SELECT 
                    p.id, p.name, p.species, p.breed, p.sex, p.birth_date,
                    o.full_name as owner_name, p.weight_kg
                FROM clinic_pet p
                LEFT JOIN clinic_owner o ON p.owner_id = o.id
                ORDER BY p.id DESC
            """)
            self.pet_data = cursor.fetchall()
            self.display_pets(self.pet_data)
            
            # Load superadmins
            cursor.execute("""
                SELECT 
                    s.id, u.username, s.email,
                    s.full_name, s.created_at, s.is_active,
                    u.id as user_id
                FROM vet_superadmin s
                JOIN auth_user u ON s.user_id = u.id
                ORDER BY s.id DESC
            """)
            self.superadmin_data = cursor.fetchall()
            self.display_superadmins(self.superadmin_data)
            
            # Update statistics
            try:
                pending_count = sum(1 for v in self.vet_data if v['approval_status'] != 'approved')
                
                # Update stat cards
                self.update_stat_card(self.total_vets_card, len(self.vet_data))
                self.update_stat_card(self.pending_vets_card, pending_count)
                self.update_stat_card(self.total_owners_card, len(self.owner_data))
                
                # Update branch stats
                branch_counts = {'taguig': 0, 'pasig': 0, 'makati': 0}
                for v in self.vet_data:
                    branch = v.get('branch', '').lower() if v.get('branch') else ''
                    if branch in branch_counts:
                        branch_counts[branch] += 1
                
                self.update_stat_card(self.branch_stats['taguig'], f"{branch_counts['taguig']} Vets")
                self.update_stat_card(self.branch_stats['pasig'], f"{branch_counts['pasig']} Vets")
                self.update_stat_card(self.branch_stats['makati'], f"{branch_counts['makati']} Vets")
                
                # Update report statistics
                self.update_report_statistics(cursor, conn)
            except Exception as stat_err:
                logger.error(f"Error calculating statistics: {stat_err}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            import traceback
            logger.error(f"Error loading data: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.show_error_dialog("Error", f"Failed to load data: {str(e)}")
    
    def update_report_statistics(self, cursor=None, conn=None):
        """Update statistics for the reports tab"""
        try:
            close_conn = False
            if not conn:
                conn = get_connection()
                cursor = conn.cursor()
                close_conn = True
            
            # Get counts
            cursor.execute("SELECT COUNT(*) as count FROM auth_user")
            total_users = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM vet_veterinarian")
            total_vets = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM clinic_owner")
            total_owners = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM clinic_pet")
            total_pets = cursor.fetchone()['count']
            
            # Update labels in stat cards
            self.report_total_users.findChild(QLabel, "stat_total_users").setText(str(total_users))
            self.report_total_vets.findChild(QLabel, "stat_total_vets").setText(str(total_vets))
            self.report_total_owners.findChild(QLabel, "stat_total_owners").setText(str(total_owners))
            self.report_total_pets.findChild(QLabel, "stat_total_pets").setText(str(total_pets))
            
            if close_conn:
                cursor.close()
                conn.close()
        except Exception as e:
            logger.error(f"Error updating report statistics: {e}")
    
    def display_vets(self, data):
        """Display veterinarians in the table with branch info"""
        self.vets_table.setRowCount(0)
        
        # Branch colors for badges
        branch_colors = {
            'taguig': self.COLORS['taguig'],
            'pasig': self.COLORS['pasig'],
            'makati': self.COLORS['makati'],
        }
        
        for row_idx, row_data in enumerate(data):
            try:
                self.vets_table.insertRow(row_idx)
                
                # Handle dict-like cursor results (RealDictRow from psycopg2)
                vet_id = row_data['id']
                username = row_data['username']
                email = row_data['email']
                full_name = row_data['full_name']
                branch = row_data.get('branch', 'N/A') or 'N/A'
                specialization = row_data.get('specialization', 'N/A')
                license_number = row_data.get('license_number', 'N/A')
                access_code = row_data['access_code']
                approval_status = row_data['approval_status']
                user_id = row_data.get('user_id')
                
                # ID, Username, Email, Full Name
                values = [vet_id, username, email, full_name]
                for col_idx, value in enumerate(values):
                    item = QTableWidgetItem(str(value) if value else "N/A")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.vets_table.setItem(row_idx, col_idx, item)
                
                # Branch (column 4) - with color
                branch_display = branch.title() if branch and branch != 'N/A' else 'N/A'
                branch_item = QTableWidgetItem(f"📍 {branch_display}")
                branch_item.setFlags(branch_item.flags() & ~Qt.ItemIsEditable)
                branch_color = branch_colors.get(branch.lower() if branch else '', '#64748b')
                branch_item.setForeground(QColor(branch_color))
                branch_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.vets_table.setItem(row_idx, 4, branch_item)
                
                # Specialization, License # (columns 5, 6)
                spec_item = QTableWidgetItem(str(specialization) if specialization else "N/A")
                spec_item.setFlags(spec_item.flags() & ~Qt.ItemIsEditable)
                self.vets_table.setItem(row_idx, 5, spec_item)
                
                license_item = QTableWidgetItem(str(license_number) if license_number else "N/A")
                license_item.setFlags(license_item.flags() & ~Qt.ItemIsEditable)
                self.vets_table.setItem(row_idx, 6, license_item)
                
                # Access Code (column 7)
                access_code_text = access_code if access_code else "Not Set"
                access_item = QTableWidgetItem(access_code_text)
                access_item.setFlags(access_item.flags() & ~Qt.ItemIsEditable)
                access_item.setFont(QFont("Courier", 9, QFont.Bold))
                access_item.setForeground(QColor(self.COLORS['primary']))
                self.vets_table.setItem(row_idx, 7, access_item)
                
                # Status (column 8)
                status_map = {
                    'approved': ('✓ Approved', self.COLORS['success']),
                    'pending': ('⏳ Pending', self.COLORS['warning']),
                    'rejected': ('✗ Rejected', self.COLORS['danger'])
                }
                status_text, status_color = status_map.get(approval_status, ('⏳ Pending', self.COLORS['warning']))
                status_item = QTableWidgetItem(status_text)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setForeground(QColor(status_color))
                status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.vets_table.setItem(row_idx, 8, status_item)
                
                # Actions widget (column 9)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(3)
                
                # Approve/Reject buttons for pending vets
                if approval_status == 'pending':
                    approve_btn = QPushButton("Approve")
                    approve_btn.setToolTip("Approve this vet")
                    approve_btn.setCursor(Qt.PointingHandCursor)
                    approve_btn.setMinimumWidth(60)
                    approve_btn.setStyleSheet(f"""
                        QPushButton {{ background: {self.COLORS['success']}; color: white; padding: 5px 8px; border-radius: 4px; font-weight: bold; border: none; font-size: 11px; }}
                        QPushButton:hover {{ background: #059669; }}
                    """)
                    approve_btn.clicked.connect(lambda checked, vid=vet_id: self.approve_vet(vid))
                    actions_layout.addWidget(approve_btn)
                    
                    reject_btn = QPushButton("Reject")
                    reject_btn.setToolTip("Reject this vet")
                    reject_btn.setCursor(Qt.PointingHandCursor)
                    reject_btn.setMinimumWidth(55)
                    reject_btn.setStyleSheet(f"""
                        QPushButton {{ background: {self.COLORS['danger']}; color: white; padding: 5px 8px; border-radius: 4px; font-weight: bold; border: none; font-size: 11px; }}
                        QPushButton:hover {{ background: #dc2626; }}
                    """)
                    reject_btn.clicked.connect(lambda checked, vid=vet_id: self.reject_vet(vid))
                    actions_layout.addWidget(reject_btn)
                
                # Edit button
                edit_btn = QPushButton("Edit")
                edit_btn.setToolTip("Edit user details")
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.setMinimumWidth(45)
                edit_btn.setStyleSheet(f"""
                    QPushButton {{ background: {self.COLORS['primary']}; color: white; padding: 5px 8px; border-radius: 4px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: {self.COLORS['primary_dark']}; }}
                """)
                edit_btn.clicked.connect(lambda checked, uid=user_id, utype='vet': self.edit_user(uid, utype))
                actions_layout.addWidget(edit_btn)
                
                # Reset password button
                reset_btn = QPushButton("Reset")
                reset_btn.setToolTip("Reset password")
                reset_btn.setCursor(Qt.PointingHandCursor)
                reset_btn.setMinimumWidth(50)
                reset_btn.setStyleSheet(f"""
                    QPushButton {{ background: {self.COLORS['text_secondary']}; color: white; padding: 5px 8px; border-radius: 4px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: #475569; }}
                """)
                reset_btn.clicked.connect(lambda checked, uid=user_id: self.reset_password(uid))
                actions_layout.addWidget(reset_btn)
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setToolTip("Delete user permanently")
                delete_btn.setCursor(Qt.PointingHandCursor)
                delete_btn.setMinimumWidth(50)
                delete_btn.setStyleSheet(f"""
                    QPushButton {{ background: {self.COLORS['danger']}; color: white; padding: 5px 8px; border-radius: 4px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: #dc2626; }}
                """)
                delete_btn.clicked.connect(lambda checked, uid=user_id, utype='vet': self.delete_user(uid, utype))
                actions_layout.addWidget(delete_btn)
                
                self.vets_table.setCellWidget(row_idx, 9, actions_widget)
                
            except Exception as e:
                logger.error(f"Error displaying vet row {row_idx}: {e}")
                logger.error(f"Row data type: {type(row_data)}, Row data: {row_data}")
    
    def display_owners(self, data):
        """Display pet owners in the table with branch info"""
        self.owners_table.setRowCount(0)
        
        # Branch colors for badges
        branch_colors = {
            'taguig': self.COLORS['taguig'],
            'pasig': self.COLORS['pasig'],
            'makati': self.COLORS['makati'],
        }
        
        for row_idx, row_data in enumerate(data):
            try:
                self.owners_table.insertRow(row_idx)
                
                # Handle dict-like cursor results (RealDictRow from psycopg2)
                owner_id = row_data['id']
                username = row_data['username']
                email = row_data['email']
                full_name = row_data['full_name']
                branch = row_data.get('branch', 'N/A') or 'N/A'
                phone = row_data['phone']
                address = row_data.get('address', 'N/A')
                is_active = row_data['is_active']
                user_id = row_data.get('user_id')
                
                # ID, Username, Email, Full Name
                values = [owner_id, username, email, full_name]
                for col_idx, value in enumerate(values):
                    display_value = str(value) if value else "N/A"
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.owners_table.setItem(row_idx, col_idx, item)
                
                # Branch (column 4) - with color
                branch_display = branch.title() if branch and branch != 'N/A' else 'N/A'
                branch_item = QTableWidgetItem(f"📍 {branch_display}")
                branch_item.setFlags(branch_item.flags() & ~Qt.ItemIsEditable)
                branch_color = branch_colors.get(branch.lower() if branch else '', '#64748b')
                branch_item.setForeground(QColor(branch_color))
                branch_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.owners_table.setItem(row_idx, 4, branch_item)
                
                # Phone, Address (columns 5, 6)
                phone_item = QTableWidgetItem(str(phone) if phone else "N/A")
                phone_item.setFlags(phone_item.flags() & ~Qt.ItemIsEditable)
                self.owners_table.setItem(row_idx, 5, phone_item)
                
                address_item = QTableWidgetItem(str(address) if address else "N/A")
                address_item.setFlags(address_item.flags() & ~Qt.ItemIsEditable)
                self.owners_table.setItem(row_idx, 6, address_item)
                
                # Status (column 7)
                status_text = "✓ Active" if is_active else "✗ Inactive"
                status_item = QTableWidgetItem(status_text)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setForeground(QColor(self.COLORS['success'] if is_active else self.COLORS['danger']))
                status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.owners_table.setItem(row_idx, 7, status_item)
                
                # Actions widget (column 8)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(3)
                
                # Edit button
                edit_btn = QPushButton("Edit")
                edit_btn.setToolTip("Edit user details")
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.setMinimumWidth(45)
                edit_btn.setStyleSheet(f"""
                    QPushButton {{ background: {self.COLORS['primary']}; color: white; padding: 5px 8px; border-radius: 4px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: {self.COLORS['primary_dark']}; }}
                """)
                edit_btn.clicked.connect(lambda checked, uid=user_id, utype='owner': self.edit_user(uid, utype))
                actions_layout.addWidget(edit_btn)
                
                # Toggle active status
                toggle_text = "Disable" if is_active else "Enable"
                toggle_btn = QPushButton(toggle_text)
                toggle_btn.setToolTip("Deactivate" if is_active else "Activate")
                toggle_btn.setCursor(Qt.PointingHandCursor)
                toggle_btn.setMinimumWidth(55)
                toggle_btn.setStyleSheet(f"""
                    QPushButton {{ background: {self.COLORS['warning'] if is_active else self.COLORS['success']}; color: white; padding: 5px 8px; border-radius: 4px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: {'#d97706' if is_active else '#059669'}; }}
                """)
                toggle_btn.clicked.connect(lambda checked, uid=user_id, active=is_active: self.toggle_user_status(uid, not active))
                actions_layout.addWidget(toggle_btn)
                
                # Reset password button
                reset_btn = QPushButton("Reset")
                reset_btn.setToolTip("Reset password")
                reset_btn.setCursor(Qt.PointingHandCursor)
                reset_btn.setMinimumWidth(50)
                reset_btn.setStyleSheet(f"""
                    QPushButton {{ background: {self.COLORS['text_secondary']}; color: white; padding: 5px 8px; border-radius: 4px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: #475569; }}
                """)
                reset_btn.clicked.connect(lambda checked, uid=user_id: self.reset_password(uid))
                actions_layout.addWidget(reset_btn)
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setToolTip("Delete user permanently")
                delete_btn.setCursor(Qt.PointingHandCursor)
                delete_btn.setMinimumWidth(50)
                delete_btn.setStyleSheet(f"""
                    QPushButton {{ background: {self.COLORS['danger']}; color: white; padding: 5px 8px; border-radius: 4px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: #dc2626; }}
                """)
                delete_btn.clicked.connect(lambda checked, uid=user_id, utype='owner': self.delete_user(uid, utype))
                actions_layout.addWidget(delete_btn)
                
                self.owners_table.setCellWidget(row_idx, 8, actions_widget)
                
            except Exception as e:
                logger.error(f"Error displaying owner row {row_idx}: {e}")
                logger.error(f"Row data type: {type(row_data)}, Row data: {row_data}")
    
    def approve_vet(self, vet_id):
        """Approve a veterinarian"""
        if not self.show_confirm_dialog(
            "Confirm Approval",
            f"Are you sure you want to approve Veterinarian ID {vet_id}?\n\nThey will be able to login immediately.",
            confirm_text="Approve",
            is_danger=False
        ):
            return
        
        try:
            conn = get_connection()
            if not conn:
                self.show_error_dialog("Error", "Failed to connect to database")
                return
            
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vet_veterinarian 
                SET approval_status = 'approved'
                WHERE id = %s
            """, (vet_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            self.show_info_dialog("Success", f"Veterinarian ID {vet_id} has been approved!\nThey can now login to the system.")
            
            # Reload data
            self.load_data()
            
        except Exception as e:
            logger.error(f"Error approving vet: {e}")
            self.show_error_dialog("Error", f"Failed to approve vet: {str(e)}")
    
    def filter_vets(self, text):
        """Filter veterinarians table"""
        if not text:
            self.display_vets(self.vet_data)
            return
        
        text = text.lower()
        filtered_data = [
            row for row in self.vet_data
            if text in str(row['username']).lower() or
               text in str(row['email']).lower() or
               text in str(row['full_name']).lower()
        ]
        self.display_vets(filtered_data)
    
    def filter_owners(self, text):
        """Filter pet owners table"""
        if not text:
            self.display_owners(self.owner_data)
            return
        
        text = text.lower()
        filtered_data = [
            row for row in self.owner_data
            if text in str(row['username']).lower() or
               text in str(row['email']).lower() or
               text in str(row['full_name']).lower()
        ]
        self.display_owners(filtered_data)
    
    def filter_vets_by_status(self, status):
        """Filter veterinarians by approval status"""
        if status == "All Status":
            self.display_vets(self.vet_data)
            return
        
        status_map = {"Approved": "approved", "Pending": "pending", "Rejected": "rejected"}
        filter_status = status_map.get(status, "pending")
        
        filtered_data = [
            row for row in self.vet_data
            if row['approval_status'] == filter_status
        ]
        self.display_vets(filtered_data)
    
    def filter_vets_by_branch(self, branch):
        """Filter veterinarians by branch"""
        if branch == "All Branches":
            self.display_vets(self.vet_data)
            return
        
        branch_lower = branch.lower()
        filtered_data = [
            row for row in self.vet_data
            if (row.get('branch') or '').lower() == branch_lower
        ]
        self.display_vets(filtered_data)
    
    def filter_owners_by_branch(self, branch):
        """Filter pet owners by branch"""
        if branch == "All Branches":
            self.display_owners(self.owner_data)
            return
        
        branch_lower = branch.lower()
        filtered_data = [
            row for row in self.owner_data
            if (row.get('branch') or '').lower() == branch_lower
        ]
        self.display_owners(filtered_data)
    
    def display_pets(self, data):
        """Display pets in the table"""
        self.pets_table.setRowCount(0)
        
        for row_idx, row_data in enumerate(data):
            try:
                self.pets_table.insertRow(row_idx)
                
                pet_id = row_data['id']
                name = row_data['name']
                species = row_data['species']
                breed = row_data.get('breed', 'N/A')
                sex = row_data.get('sex', 'N/A')
                birth_date = row_data.get('birth_date', 'N/A')
                owner_name = row_data.get('owner_name', 'Unknown')
                weight_kg = row_data.get('weight_kg', 'N/A')
                
                values = [pet_id, name, species, breed, sex, birth_date, owner_name, weight_kg]
                for col_idx, value in enumerate(values):
                    display_value = str(value) if value else "N/A"
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.pets_table.setItem(row_idx, col_idx, item)
                    
            except Exception as e:
                logger.error(f"Error displaying pet row {row_idx}: {e}")
    
    def filter_pets(self, text):
        """Filter pets table"""
        if not text:
            self.display_pets(self.pet_data)
            return
        
        text = text.lower()
        filtered_data = [
            row for row in self.pet_data
            if text in str(row['name']).lower() or
               text in str(row['species']).lower() or
               text in str(row.get('owner_name', '')).lower()
        ]
        self.display_pets(filtered_data)
    
    def display_superadmins(self, data):
        """Display superadmins in the table"""
        self.superadmins_table.setRowCount(0)
        
        for row_idx, row_data in enumerate(data):
            try:
                self.superadmins_table.insertRow(row_idx)
                
                sa_id = row_data['id']
                username = row_data['username']
                email = row_data['email']
                full_name = row_data['full_name']
                created_at = row_data.get('created_at', 'N/A')
                user_id = row_data.get('user_id')
                
                # Format created_at
                if created_at and created_at != 'N/A':
                    try:
                        from datetime import datetime
                        if isinstance(created_at, str):
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            dt = created_at
                        created_at = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                values = [sa_id, username, email, full_name, created_at]
                for col_idx, value in enumerate(values):
                    display_value = str(value) if value else "N/A"
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.superadmins_table.setItem(row_idx, col_idx, item)
                
                # Actions column
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(6)
                
                # Edit button
                edit_btn = QPushButton("Edit")
                edit_btn.setMinimumWidth(60)
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {self.COLORS['primary']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background: {self.COLORS['primary_dark']};
                    }}
                """)
                edit_btn.clicked.connect(lambda checked, sid=sa_id: self.edit_superadmin(sid))
                actions_layout.addWidget(edit_btn)
                
                # Reset password button
                reset_btn = QPushButton("Reset")
                reset_btn.setMinimumWidth(60)
                reset_btn.setCursor(Qt.PointingHandCursor)
                reset_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {self.COLORS['warning']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background: #d97706;
                    }}
                """)
                reset_btn.clicked.connect(lambda checked, uid=user_id: self.reset_password(uid))
                actions_layout.addWidget(reset_btn)
                
                # Delete button (only show if more than 1 superadmin)
                if len(data) > 1:
                    delete_btn = QPushButton("Delete")
                    delete_btn.setMinimumWidth(60)
                    delete_btn.setCursor(Qt.PointingHandCursor)
                    delete_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {self.COLORS['danger']};
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-size: 11px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background: #dc2626;
                        }}
                    """)
                    delete_btn.clicked.connect(lambda checked, sid=sa_id, uid=user_id: self.delete_superadmin(sid, uid))
                    actions_layout.addWidget(delete_btn)
                
                self.superadmins_table.setCellWidget(row_idx, 5, actions_widget)
                
            except Exception as e:
                logger.error(f"Error displaying superadmin row {row_idx}: {e}")
    
    def edit_superadmin(self, superadmin_id):
        """Edit a superadmin"""
        # Find the superadmin data
        sa_data = next((s for s in self.superadmin_data if s['id'] == superadmin_id), None)
        if not sa_data:
            self.show_error_dialog("Error", "Superadmin not found")
            return
        
        dialog = EditSuperadminDialog(superadmin_id, sa_data, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
    
    def delete_superadmin(self, superadmin_id, user_id):
        """Delete a superadmin"""
        if len(self.superadmin_data) <= 1:
            self.show_error_dialog("Error", "Cannot delete the last superadmin account!")
            return
        
        if not self.show_confirm_dialog(
            "Confirm Delete",
            "Are you sure you want to delete this superadmin account?\n\nThis action cannot be undone.",
            confirm_text="Delete",
            is_danger=True
        ):
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Delete superadmin profile
            cursor.execute("DELETE FROM vet_superadmin WHERE id = %s", (superadmin_id,))
            
            # Delete the auth_user account
            cursor.execute("DELETE FROM auth_user WHERE id = %s", (user_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.show_info_dialog("Success", "Superadmin deleted successfully!")
            self.load_data()
            
        except Exception as e:
            logger.error(f"Error deleting superadmin: {e}")
            self.show_error_dialog("Error", f"Failed to delete superadmin: {str(e)}")
    
    def display_appointments(self, data):
        """Display appointments in the table"""
        self.appointments_table.setRowCount(0)
        
        for row_idx, row_data in enumerate(data):
            try:
                self.appointments_table.insertRow(row_idx)
                
                appt_id = row_data['id']
                pet_name = row_data.get('pet_name', 'Unknown')
                owner_name = row_data.get('owner_name', 'Unknown')
                vet_name = row_data.get('vet_name', 'N/A')
                date_time = row_data.get('date_time', 'N/A')
                reason = row_data.get('reason', 'N/A')
                status = row_data.get('status', 'scheduled')
                
                values = [appt_id, pet_name, owner_name, vet_name, date_time, reason]
                for col_idx, value in enumerate(values):
                    display_value = str(value) if value else "N/A"
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.appointments_table.setItem(row_idx, col_idx, item)
                
                # Status column with color
                status_colors = {
                    'scheduled': '#ffc107',
                    'completed': '#28a745',
                    'cancelled': '#dc3545'
                }
                status_item = QTableWidgetItem(status.capitalize() if status else "Scheduled")
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setForeground(QColor(status_colors.get(status, '#6c757d')))
                status_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.appointments_table.setItem(row_idx, 6, status_item)
                
            except Exception as e:
                logger.error(f"Error displaying appointment row {row_idx}: {e}")
    
    def filter_appointments(self, status):
        """Filter appointments by status"""
        if status == "All":
            self.display_appointments(self.appointment_data)
            return
        
        filter_status = status.lower()
        filtered_data = [
            row for row in self.appointment_data
            if row.get('status', 'scheduled') == filter_status
        ]
        self.display_appointments(filtered_data)
    
    def edit_user(self, user_id, user_type):
        """Edit user details"""
        if not user_id:
            self.show_error_dialog("Error", "User ID not found")
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if user_type == 'vet':
                cursor.execute("""
                    SELECT u.username, u.email, v.full_name, v.specialization, v.license_number
                    FROM auth_user u
                    JOIN vet_veterinarian v ON v.user_id = u.id
                    WHERE u.id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT u.username, u.email, o.full_name, o.phone, o.address
                    FROM auth_user u
                    JOIN clinic_owner o ON o.user_id = u.id
                    WHERE u.id = %s
                """, (user_id,))
            
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user_data:
                self.show_error_dialog("Error", "User not found")
                return
            
            dialog = EditUserDialog(user_id, user_data, user_type, self)
            if dialog.exec() == QDialog.Accepted:
                self.load_data()  # Refresh data
                
        except Exception as e:
            logger.error(f"Error editing user: {e}")
            self.show_error_dialog("Error", f"Failed to edit user: {str(e)}")
    
    def delete_user(self, user_id, user_type):
        """Delete a user and ALL related data completely from database"""
        if not user_id:
            self.show_error_dialog("Error", "User ID not found")
            return
        
        # Create custom confirmation dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Confirm Delete")
        dialog.setFixedSize(400, 280)
        dialog.setStyleSheet(f"""
            QDialog {{
                background: {self.COLORS['surface']};
            }}
            QLabel {{
                color: {self.COLORS['text']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Warning icon and title
        title = QLabel(f"⚠️ Delete {user_type.title()}?")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.COLORS['danger']};")
        layout.addWidget(title)
        
        # Warning message
        message = QLabel(
            f"This will permanently delete:\n\n"
            f"• The user account\n"
            f"• {'All their pets and pet data' if user_type == 'owner' else 'Veterinarian profile'}\n"
            f"• All appointments\n"
            f"• All medical records\n"
            f"• All notifications"
        )
        message.setStyleSheet("font-size: 13px; line-height: 1.5;")
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Warning box
        warning = QLabel("⚠️ THIS ACTION CANNOT BE UNDONE!")
        warning.setStyleSheet(f"""
            background: #fef2f2;
            color: {self.COLORS['danger']};
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 12px;
        """)
        warning.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(120, 40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['bg']};
                color: {self.COLORS['text']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {self.COLORS['border']};
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        delete_btn = QPushButton("Yes, Delete")
        delete_btn.setFixedSize(120, 40)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['danger']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #dc2626;
            }}
        """)
        delete_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog and check result
        if dialog.exec() == QDialog.Accepted:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                if user_type == 'owner':
                    # Get the owner ID first
                    cursor.execute("SELECT id FROM clinic_owner WHERE user_id = %s", (user_id,))
                    owner_result = cursor.fetchone()
                    
                    if owner_result:
                        owner_id = owner_result['id']
                        
                        # Get all pet IDs for this owner
                        cursor.execute("SELECT id FROM clinic_pet WHERE owner_id = %s", (owner_id,))
                        pet_ids = [row['id'] for row in cursor.fetchall()]
                        
                        if pet_ids:
                            # Delete medical records for all pets
                            cursor.execute(
                                "DELETE FROM clinic_medicalrecord WHERE pet_id IN %s",
                                (tuple(pet_ids),)
                            )
                            
                            # Delete appointments for all pets
                            cursor.execute(
                                "DELETE FROM clinic_appointment WHERE pet_id IN %s",
                                (tuple(pet_ids),)
                            )
                            
                            # Delete all pets
                            cursor.execute(
                                "DELETE FROM clinic_pet WHERE owner_id = %s",
                                (owner_id,)
                            )
                        
                        # Delete notifications for this owner
                        cursor.execute(
                            "DELETE FROM clinic_notification WHERE owner_id = %s",
                            (owner_id,)
                        )
                        
                        # Delete the owner profile
                        cursor.execute(
                            "DELETE FROM clinic_owner WHERE id = %s",
                            (owner_id,)
                        )
                
                elif user_type == 'vet':
                    # Get the vet ID first
                    cursor.execute("SELECT id FROM vet_veterinarian WHERE user_id = %s", (user_id,))
                    vet_result = cursor.fetchone()
                    
                    if vet_result:
                        vet_id = vet_result['id']
                        
                        # Delete the veterinarian profile
                        # Note: Appointments don't have a veterinarian FK in this schema
                        cursor.execute(
                            "DELETE FROM vet_veterinarian WHERE id = %s",
                            (vet_id,)
                        )
                
                # Finally delete the auth_user account
                cursor.execute("DELETE FROM auth_user WHERE id = %s", (user_id,))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                self.show_info_dialog(
                    "Success", 
                    f"{user_type.capitalize()} and all related data deleted permanently!"
                )
                self.load_data()
                
            except Exception as e:
                logger.error(f"Error deleting user: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                self.show_error_dialog("Error", f"Failed to delete user: {str(e)}")
    
    def reset_password(self, user_id):
        """Reset user password"""
        if not user_id:
            self.show_error_dialog("Error", "User ID not found")
            return
        
        dialog = ResetPasswordDialog(user_id, self)
        if dialog.exec() == QDialog.Accepted:
            self.show_info_dialog("Success", "Password has been reset!")
    
    def toggle_user_status(self, user_id, new_status):
        """Toggle user active status"""
        if not user_id:
            self.show_error_dialog("Error", "User ID not found")
            return
        
        status_text = "activate" if new_status else "deactivate"
        if not self.show_confirm_dialog(
            "Confirm Status Change",
            f"Are you sure you want to {status_text} this user?",
            confirm_text=status_text.title(),
            is_danger=not new_status
        ):
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE auth_user SET is_active = %s WHERE id = %s",
                (new_status, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            self.show_info_dialog("Success", f"User {status_text}d successfully!")
            self.load_data()
            
        except Exception as e:
            logger.error(f"Error toggling user status: {e}")
            self.show_error_dialog("Error", f"Failed to {status_text} user: {str(e)}")
    
    def reject_vet(self, vet_id):
        """Reject a veterinarian"""
        if not self.show_confirm_dialog(
            "Confirm Rejection",
            f"Are you sure you want to reject Veterinarian ID {vet_id}?\n\nThey will not be able to login.",
            confirm_text="Reject",
            is_danger=True
        ):
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vet_veterinarian 
                SET approval_status = 'rejected'
                WHERE id = %s
            """, (vet_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            self.show_info_dialog("Success", f"Veterinarian ID {vet_id} has been rejected.")
            self.load_data()
            
        except Exception as e:
            logger.error(f"Error rejecting vet: {e}")
            self.show_error_dialog("Error", f"Failed to reject vet: {str(e)}")
    
    def export_report(self):
        """Export system report to CSV"""
        try:
            import csv
            from datetime import datetime
            
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(reports_dir, f"system_report_{timestamp}.csv")
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(["ePetCare System Report"])
                writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([])
                
                # Veterinarians section
                writer.writerow(["=== VETERINARIANS ==="])
                writer.writerow(["ID", "Username", "Email", "Full Name", "Specialization", "License #", "Status"])
                for vet in self.vet_data:
                    writer.writerow([
                        vet['id'], vet['username'], vet['email'], vet['full_name'],
                        vet.get('specialization', 'N/A'), vet.get('license_number', 'N/A'),
                        vet['approval_status']
                    ])
                writer.writerow([])
                
                # Pet Owners section
                writer.writerow(["=== PET OWNERS ==="])
                writer.writerow(["ID", "Username", "Email", "Full Name", "Phone", "Address", "Status"])
                for owner in self.owner_data:
                    writer.writerow([
                        owner['id'], owner['username'], owner['email'], owner['full_name'],
                        owner['phone'], owner.get('address', 'N/A'),
                        "Active" if owner['is_active'] else "Inactive"
                    ])
                writer.writerow([])
                
                # Pets section
                writer.writerow(["=== PETS ==="])
                writer.writerow(["ID", "Name", "Species", "Breed", "Sex", "Birth Date", "Owner", "Weight"])
                for pet in self.pet_data:
                    writer.writerow([
                        pet['id'], pet['name'], pet['species'], pet.get('breed', 'N/A'),
                        pet.get('sex', 'N/A'), pet.get('birth_date', 'N/A'),
                        pet.get('owner_name', 'Unknown'), pet.get('weight_kg', 'N/A')
                    ])
            
            self.show_info_dialog(
                "Report Exported",
                f"Report saved to:\n{filename}"
            )
            
            # Open the reports folder
            import subprocess
            subprocess.Popen(f'explorer /select,"{filename}"')
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            self.show_error_dialog("Error", f"Failed to export report: {str(e)}")
