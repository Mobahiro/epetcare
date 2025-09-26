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
from utils.pg_db import get_connection as get_pg_connection


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
        
        # PostgreSQL settings (read-only summary for now; editing via config.json)
        pg_group = QGroupBox("PostgreSQL Connection")
        pg_layout = QFormLayout()
        pg_cfg = self.config.get('postgres', {})

        self.pg_host_edit = QLineEdit(pg_cfg.get('host', ''))
        self.pg_host_edit.setReadOnly(True)
        pg_layout.addRow("Host:", self.pg_host_edit)

        self.pg_db_edit = QLineEdit(pg_cfg.get('database', ''))
        self.pg_db_edit.setReadOnly(True)
        pg_layout.addRow("Database:", self.pg_db_edit)

        self.pg_user_edit = QLineEdit(pg_cfg.get('user', ''))
        self.pg_user_edit.setReadOnly(True)
        pg_layout.addRow("User:", self.pg_user_edit)

        masked_pw = '********' if pg_cfg.get('password') else ''
        self.pg_pass_edit = QLineEdit(masked_pw)
        self.pg_pass_edit.setReadOnly(True)
        pg_layout.addRow("Password:", self.pg_pass_edit)

        self.pg_status_label = QLabel("Not Connected")
        try:
            conn = get_pg_connection()
            if conn:
                self.pg_status_label.setText("Connected")
        except Exception:
            pass
        pg_layout.addRow("Status:", self.pg_status_label)

        hint = QLabel("Edit credentials directly in config.json then restart application.")
        hint.setWordWrap(True)
        pg_layout.addRow("", hint)

        pg_group.setLayout(pg_layout)
        general_layout.addWidget(pg_group)
        
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
    
    # Removed browse / backup actions (SQLite legacy)
    
    def save_settings(self):
        """Save the settings"""
        # Update config
        self.config['app']['offline_mode'] = self.offline_mode_check.isChecked()
        self.config['app']['sync_interval'] = self.sync_interval_spin.value()
        self.config['app']['auto_backup'] = self.auto_backup_check.isChecked()
        
        # Store previous theme and font size to detect changes
        previous_theme = self.config['ui']['theme']
        previous_font_size = self.config['ui']['font_size']
        
        # Update UI settings
        self.config['ui']['theme'] = self.theme_combo.currentData()
        self.config['ui']['font_size'] = self.font_size_spin.value()
        
        # Check if theme or font size changed
        theme_changed = previous_theme != self.config['ui']['theme']
        font_size_changed = previous_font_size != self.config['ui']['font_size']
        
        # Save to file
        if save_config(self.config):
            # Apply theme changes if needed
            if theme_changed or font_size_changed:
                try:
                    from utils.theme_manager import apply_theme, update_font_size
                    from PySide6.QtWidgets import QApplication
                    
                    app = QApplication.instance()
                    if app:
                        if theme_changed:
                            apply_theme(app)
                        if font_size_changed:
                            update_font_size(app)
                        
                        QMessageBox.information(
                            self,
                            "Settings Saved",
                            "Settings have been saved and applied successfully."
                        )
                    else:
                        QMessageBox.information(
                            self,
                            "Settings Saved",
                            "Settings have been saved successfully.\n"
                            "Some changes will take effect after restarting the application."
                        )
                except Exception as e:
                    QMessageBox.information(
                        self,
                        "Settings Saved",
                        f"Settings have been saved, but could not apply theme changes: {e}\n"
                        "Please restart the application for changes to take effect."
                    )
            else:
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    "Settings have been saved successfully."
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
        self.offline_mode_check.setChecked(self.config['app']['offline_mode'])
        self.sync_interval_spin.setValue(self.config['app']['sync_interval'])
        self.auto_backup_check.setChecked(self.config['app']['auto_backup'])
        
        index = self.theme_combo.findData(self.config['ui']['theme'])
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self.font_size_spin.setValue(self.config['ui']['font_size'])
