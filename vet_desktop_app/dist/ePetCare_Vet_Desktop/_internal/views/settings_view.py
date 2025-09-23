"""
Settings view for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QSpinBox,
    QComboBox, QFileDialog, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont

from utils.config import load_config, save_config, get_config_value, set_config_value
from utils.database import backup_database


class SettingsView(QWidget):
    """Settings view for configuring application settings"""
    
    def __init__(self, user, veterinarian):
        super().__init__()
        self.user = user
        self.veterinarian = veterinarian
        self.config = load_config()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("Settings")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header_label)
        
        # Tabs
        tabs = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Database settings
        db_group = QGroupBox("Database")
        db_layout = QFormLayout()
        
        self.db_path_edit = QLineEdit(self.config['database']['path'])
        self.db_path_edit.setReadOnly(True)
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        
        self.browse_db_button = QPushButton("Browse...")
        self.browse_db_button.clicked.connect(self.browse_db_path)
        db_path_layout.addWidget(self.browse_db_button)
        
        db_layout.addRow("Database Path:", db_path_layout)
        
        self.backup_dir_edit = QLineEdit(self.config['database']['backup_dir'])
        self.backup_dir_edit.setReadOnly(True)
        
        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(self.backup_dir_edit)
        
        self.browse_backup_button = QPushButton("Browse...")
        self.browse_backup_button.clicked.connect(self.browse_backup_dir)
        backup_dir_layout.addWidget(self.browse_backup_button)
        
        db_layout.addRow("Backup Directory:", backup_dir_layout)
        
        self.backup_now_button = QPushButton("Backup Now")
        self.backup_now_button.clicked.connect(self.backup_now)
        db_layout.addRow("", self.backup_now_button)
        
        db_group.setLayout(db_layout)
        general_layout.addWidget(db_group)
        
        # Application settings
        app_group = QGroupBox("Application")
        app_layout = QFormLayout()
        
        self.offline_mode_check = QCheckBox()
        self.offline_mode_check.setChecked(self.config['app']['offline_mode'])
        app_layout.addRow("Offline Mode:", self.offline_mode_check)
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(60, 3600)
        self.sync_interval_spin.setValue(self.config['app']['sync_interval'])
        self.sync_interval_spin.setSuffix(" seconds")
        app_layout.addRow("Sync Interval:", self.sync_interval_spin)
        
        self.auto_backup_check = QCheckBox()
        self.auto_backup_check.setChecked(self.config['app']['auto_backup'])
        app_layout.addRow("Auto Backup:", self.auto_backup_check)
        
        app_group.setLayout(app_layout)
        general_layout.addWidget(app_group)
        
        # UI settings
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        current_theme = self.config['ui']['theme']
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        ui_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(self.config['ui']['font_size'])
        ui_layout.addRow("Font Size:", self.font_size_spin)
        
        ui_group.setLayout(ui_layout)
        general_layout.addWidget(ui_group)
        
        general_layout.addStretch()
        tabs.addTab(general_tab, "General")
        
        # User profile tab
        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        
        profile_group = QGroupBox("User Profile")
        profile_form = QFormLayout()
        
        self.username_label = QLabel(self.user.username)
        profile_form.addRow("Username:", self.username_label)
        
        self.name_label = QLabel(f"{self.user.first_name} {self.user.last_name}")
        profile_form.addRow("Name:", self.name_label)
        
        self.email_label = QLabel(self.user.email)
        profile_form.addRow("Email:", self.email_label)
        
        profile_group.setLayout(profile_form)
        profile_layout.addWidget(profile_group)
        
        vet_group = QGroupBox("Veterinarian Profile")
        vet_form = QFormLayout()
        
        self.vet_name_label = QLabel(self.veterinarian.full_name)
        vet_form.addRow("Full Name:", self.vet_name_label)
        
        self.specialization_label = QLabel(self.veterinarian.specialization)
        vet_form.addRow("Specialization:", self.specialization_label)
        
        self.license_label = QLabel(self.veterinarian.license_number)
        vet_form.addRow("License Number:", self.license_label)
        
        self.phone_label = QLabel(self.veterinarian.phone)
        vet_form.addRow("Phone:", self.phone_label)
        
        vet_group.setLayout(vet_form)
        profile_layout.addWidget(vet_group)
        
        profile_layout.addStretch()
        tabs.addTab(profile_tab, "Profile")
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_changes)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def browse_db_path(self):
        """Browse for database file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database File",
            self.db_path_edit.text(),
            "SQLite Database (*.sqlite3);;All Files (*)"
        )
        
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def browse_backup_dir(self):
        """Browse for backup directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            self.backup_dir_edit.text()
        )
        
        if dir_path:
            self.backup_dir_edit.setText(dir_path)
    
    def backup_now(self):
        """Backup the database immediately"""
        success, result = backup_database(self.backup_dir_edit.text())
        
        if success:
            QMessageBox.information(
                self,
                "Backup Successful",
                f"Database backup created successfully at:\n{result}"
            )
        else:
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create database backup:\n{result}"
            )
    
    def save_settings(self):
        """Save the settings"""
        # Update config
        self.config['database']['path'] = self.db_path_edit.text()
        self.config['database']['backup_dir'] = self.backup_dir_edit.text()
        
        self.config['app']['offline_mode'] = self.offline_mode_check.isChecked()
        self.config['app']['sync_interval'] = self.sync_interval_spin.value()
        self.config['app']['auto_backup'] = self.auto_backup_check.isChecked()
        
        self.config['ui']['theme'] = self.theme_combo.currentData()
        self.config['ui']['font_size'] = self.font_size_spin.value()
        
        # Save to file
        if save_config(self.config):
            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved successfully.\n"
                "Some changes may require restarting the application."
            )
        else:
            QMessageBox.warning(
                self,
                "Save Failed",
                "Failed to save settings."
            )
    
    def cancel_changes(self):
        """Cancel changes and reload settings"""
        self.config = load_config()
        
        # Update UI
        self.db_path_edit.setText(self.config['database']['path'])
        self.backup_dir_edit.setText(self.config['database']['backup_dir'])
        
        self.offline_mode_check.setChecked(self.config['app']['offline_mode'])
        self.sync_interval_spin.setValue(self.config['app']['sync_interval'])
        self.auto_backup_check.setChecked(self.config['app']['auto_backup'])
        
        index = self.theme_combo.findData(self.config['ui']['theme'])
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self.font_size_spin.setValue(self.config['ui']['font_size'])
