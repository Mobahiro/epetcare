"""
Password Reset dialog for the ePetCare Vet Desktop application.
Sends OTP to vet's email for password reset.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import random
import string
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('epetcare')


class PasswordResetDialog(QDialog):
    """Password reset dialog with OTP verification"""

    def __init__(self, parent=None, user_data_access=None, vet_data_access=None):
        super().__init__(parent)
        self.user_data_access = user_data_access
        self.vet_data_access = vet_data_access
        self.otp = None
        self.otp_expiry = None
        self.verified_user = None

        self.setWindowTitle("ePetCare Vet Desktop - Password Reset")
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header
        header_label = QLabel("Password Reset")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        subtitle_label = QLabel("Reset your password via email OTP")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        # Stacked widget for different steps
        self.stack = QStackedWidget()

        # Step 1: Email input
        self.email_widget = self.create_email_step()
        self.stack.addWidget(self.email_widget)

        # Step 2: OTP verification
        self.otp_widget = self.create_otp_step()
        self.stack.addWidget(self.otp_widget)

        # Step 3: New password
        self.password_widget = self.create_password_step()
        self.stack.addWidget(self.password_widget)

        layout.addWidget(self.stack)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setVisible(False)
        button_layout.addWidget(self.back_button)

        self.next_button = QPushButton("Send OTP")
        self.next_button.setDefault(True)
        self.next_button.clicked.connect(self.handle_next)
        button_layout.addWidget(self.next_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def create_email_step(self):
        """Create email input step"""
        widget = QGroupBox("Step 1: Enter Email")
        layout = QFormLayout()

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your registered email")
        layout.addRow("Email:", self.email_edit)

        info_label = QLabel("We'll send a 6-digit OTP to your email address.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addRow(info_label)

        widget.setLayout(layout)
        return widget

    def create_otp_step(self):
        """Create OTP verification step"""
        widget = QGroupBox("Step 2: Verify OTP")
        layout = QFormLayout()

        self.otp_display_label = QLabel()
        self.otp_display_label.setWordWrap(True)
        layout.addRow(self.otp_display_label)

        self.otp_edit = QLineEdit()
        self.otp_edit.setPlaceholderText("Enter 6-digit OTP")
        self.otp_edit.setMaxLength(6)
        layout.addRow("OTP Code:", self.otp_edit)

        resend_layout = QHBoxLayout()
        self.resend_button = QPushButton("Resend OTP")
        self.resend_button.setFlat(True)
        self.resend_button.clicked.connect(self.resend_otp)
        resend_layout.addWidget(self.resend_button)
        resend_layout.addStretch()
        layout.addRow(resend_layout)

        widget.setLayout(layout)
        return widget

    def create_password_step(self):
        """Create new password step"""
        widget = QGroupBox("Step 3: Set New Password")
        layout = QFormLayout()

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setPlaceholderText("Enter new password")
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("New Password:", self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("Confirm new password")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Confirm Password:", self.confirm_password_edit)

        info_label = QLabel("Password must be at least 6 characters long.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addRow(info_label)

        widget.setLayout(layout)
        return widget

    def handle_next(self):
        """Handle next button click based on current step"""
        current_index = self.stack.currentIndex()

        if current_index == 0:
            # Step 1: Send OTP
            self.send_otp()
        elif current_index == 1:
            # Step 2: Verify OTP
            self.verify_otp()
        elif current_index == 2:
            # Step 3: Reset password
            self.reset_password()

    def send_otp(self):
        """Send OTP to user's email"""
        email = self.email_edit.text().strip().lower()

        if not email:
            QMessageBox.warning(self, "Error", "Please enter your email address.")
            return

        # Find user by email
        from utils.pg_db import PostgresDatabaseManager
        db = PostgresDatabaseManager()
        
        try:
            # Get user from auth_user table by email
            success, result = db.execute_query(
                "SELECT id, username, email FROM auth_user WHERE LOWER(email) = ?",
                (email,)
            )
            
            if not success or not result:
                QMessageBox.warning(
                    self,
                    "Email Not Found",
                    "No account found with this email address."
                )
                return

            user_data = result[0]
            user_id = user_data['id']
            username = user_data['username']
            user_email = user_data['email']

            # Check if user is a veterinarian
            vet = self.vet_data_access.get_by_user_id(user_id)
            if not vet:
                QMessageBox.warning(
                    self,
                    "Access Denied",
                    "This email is not registered as a veterinarian account."
                )
                return

            # Generate OTP
            self.otp = ''.join(random.choices(string.digits, k=6))
            self.otp_expiry = datetime.now() + timedelta(minutes=10)
            self.verified_user = {'id': user_id, 'username': username, 'email': user_email}

            # Send OTP via email
            self.send_otp_email(user_email, self.otp)

            # Move to next step
            self.otp_display_label.setText(
                f"OTP sent to {user_email}\n"
                f"Valid for 10 minutes."
            )
            self.stack.setCurrentIndex(1)
            self.next_button.setText("Verify OTP")
            self.back_button.setVisible(True)
            self.otp_edit.setFocus()

            logger.info(f"OTP sent to {user_email}: {self.otp}")

        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to send OTP: {str(e)}"
            )

    def send_otp_email(self, email, otp):
        """Send OTP via email"""
        try:
            from utils.email_sender import send_otp_email as send_email
            
            success = send_email(email, otp)
            
            if success:
                logger.info(f"OTP email sent successfully to {email}")
            else:
                logger.warning(f"Failed to send OTP email to {email} - displaying OTP in dialog")
                
        except Exception as e:
            logger.error(f"Error sending OTP email: {e}")
            # Don't fail the process if email fails - show OTP in dialog

    def resend_otp(self):
        """Resend OTP"""
        if self.verified_user:
            self.send_otp_email(self.verified_user['email'], self.otp)
            # Reset expiry
            self.otp_expiry = datetime.now() + timedelta(minutes=10)
            QMessageBox.information(
                self,
                "OTP Resent",
                f"OTP has been resent to {self.verified_user['email']}"
            )
            logger.info(f"OTP resent to {self.verified_user['email']}")

    def verify_otp(self):
        """Verify entered OTP"""
        entered_otp = self.otp_edit.text().strip()

        if not entered_otp:
            QMessageBox.warning(self, "Error", "Please enter the OTP code.")
            return

        # Check if OTP expired
        if datetime.now() > self.otp_expiry:
            QMessageBox.warning(
                self,
                "OTP Expired",
                "The OTP has expired. Please request a new one."
            )
            self.stack.setCurrentIndex(0)
            self.next_button.setText("Send OTP")
            self.back_button.setVisible(False)
            return

        # Verify OTP
        if entered_otp != self.otp:
            QMessageBox.warning(
                self,
                "Invalid OTP",
                "The OTP code you entered is incorrect."
            )
            return

        # OTP verified, move to password reset
        self.stack.setCurrentIndex(2)
        self.next_button.setText("Reset Password")
        self.new_password_edit.setFocus()
        logger.info(f"OTP verified for user {self.verified_user['username']}")

    def reset_password(self):
        """Reset user password"""
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not new_password or not confirm_password:
            QMessageBox.warning(
                self,
                "Error",
                "Please enter and confirm your new password."
            )
            return

        if new_password != confirm_password:
            QMessageBox.warning(
                self,
                "Error",
                "Passwords do not match."
            )
            return

        if len(new_password) < 6:
            QMessageBox.warning(
                self,
                "Error",
                "Password must be at least 6 characters long."
            )
            return

        # Update password in database
        try:
            from utils.password_hasher import make_password
            from utils.pg_db import PostgresDatabaseManager
            
            db = PostgresDatabaseManager()
            hashed_password = make_password(new_password)
            
            success = db.execute_non_query(
                "UPDATE auth_user SET password = %s WHERE id = %s",
                (hashed_password, self.verified_user['id'])
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Password reset successfully for {self.verified_user['username']}!\n"
                    f"You can now login with your new password."
                )
                logger.info(f"Password reset successful for user {self.verified_user['username']}")
                self.accept()
            else:
                raise Exception("Database update failed")

        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to reset password: {str(e)}"
            )

    def go_back(self):
        """Go back to previous step"""
        current_index = self.stack.currentIndex()
        
        if current_index > 0:
            self.stack.setCurrentIndex(current_index - 1)
            
            if current_index == 1:
                self.next_button.setText("Send OTP")
                self.back_button.setVisible(False)
            elif current_index == 2:
                self.next_button.setText("Verify OTP")
