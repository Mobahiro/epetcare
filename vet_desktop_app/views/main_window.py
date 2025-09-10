"""
Main window for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QTabWidget, QStatusBar, QMessageBox, QToolBar,
    QMenu, QDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction

from views.login_dialog import LoginDialog
from views.dashboard_view import DashboardView
from views.patients_view import PatientsView
from views.appointments_view import AppointmentsView
from views.settings_view import SettingsView
from utils.database import backup_database
from utils.notification_manager import NotificationManager


class MainWindow(QMainWindow):
    """Main window for the application"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.current_vet = None
        
        self.setWindowTitle("ePetCare Vet Desktop")
        self.setMinimumSize(1200, 800)
        self.resize(1280, 800)
        
        # Set up notification manager
        self.notification_manager = NotificationManager(self)
        self.notification_manager.new_appointment_signal.connect(self.on_new_appointment)
        
        # Set up the central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Set up the main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create the stacked widget for different views
        self.stacked_widget = QStackedWidget()
        
        # Create the status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create the toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(self.toolbar)
        
        # Create the menu bar
        self.setup_menu_bar()
        
        # Add the stacked widget to the main layout
        self.main_layout.addWidget(self.stacked_widget)
        
        # Show the login dialog
        self.show_login_dialog()
    
    def setup_menu_bar(self):
        """Set up the menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        backup_action = QAction("&Backup Database", self)
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        dashboard_action = QAction("&Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.show_view("dashboard"))
        view_menu.addAction(dashboard_action)
        
        patients_action = QAction("&Patients", self)
        patients_action.triggered.connect(lambda: self.show_view("patients"))
        view_menu.addAction(patients_action)
        
        appointments_action = QAction("&Appointments", self)
        appointments_action.triggered.connect(lambda: self.show_view("appointments"))
        view_menu.addAction(appointments_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Set up the toolbar with actions"""
        self.toolbar.clear()
        
        # Dashboard action
        dashboard_action = QAction(QIcon("resources/dashboard-icon.png"), "Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.show_view("dashboard"))
        self.toolbar.addAction(dashboard_action)
        
        # Patients action
        patients_action = QAction(QIcon("resources/patients-icon.png"), "Patients", self)
        patients_action.triggered.connect(lambda: self.show_view("patients"))
        self.toolbar.addAction(patients_action)
        
        # Appointments action
        appointments_action = QAction(QIcon("resources/appointments-icon.png"), "Appointments", self)
        appointments_action.triggered.connect(lambda: self.show_view("appointments"))
        self.toolbar.addAction(appointments_action)
        
        self.toolbar.addSeparator()
        
        # Settings action
        settings_action = QAction(QIcon("resources/settings-icon.png"), "Settings", self)
        settings_action.triggered.connect(lambda: self.show_view("settings"))
        self.toolbar.addAction(settings_action)
        
        # Logout action
        logout_action = QAction(QIcon("resources/logout-icon.png"), "Logout", self)
        logout_action.triggered.connect(self.logout)
        self.toolbar.addAction(logout_action)
    
    def show_login_dialog(self):
        """Show the login dialog"""
        dialog = LoginDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.current_user = dialog.get_user()
            self.current_vet = dialog.get_veterinarian()
            self.setup_views()
            self.setup_toolbar()
            self.show_view("dashboard")
            self.status_bar.showMessage(f"Logged in as {self.current_vet.full_name}")
            
            # Start monitoring for new appointments
            self.notification_manager.start_monitoring()
        else:
            # Exit if login is cancelled
            self.close()
    
    def setup_views(self):
        """Set up the different views"""
        # Clear any existing widgets
        while self.stacked_widget.count() > 0:
            self.stacked_widget.removeWidget(self.stacked_widget.widget(0))
        
        # Create and add views
        self.dashboard_view = DashboardView(self.current_user, self.current_vet)
        self.stacked_widget.addWidget(self.dashboard_view)
        
        self.patients_view = PatientsView(self.current_user, self.current_vet)
        self.stacked_widget.addWidget(self.patients_view)
        
        self.appointments_view = AppointmentsView(self.current_user, self.current_vet)
        self.stacked_widget.addWidget(self.appointments_view)
        
        self.settings_view = SettingsView(self.current_user, self.current_vet)
        self.stacked_widget.addWidget(self.settings_view)
    
    def show_view(self, view_name):
        """Show the specified view"""
        # Check if views have been created
        if not hasattr(self, 'dashboard_view'):
            # Views haven't been set up yet
            return
            
        if view_name == "dashboard":
            self.stacked_widget.setCurrentWidget(self.dashboard_view)
            self.dashboard_view.refresh_data()
        elif view_name == "patients":
            self.stacked_widget.setCurrentWidget(self.patients_view)
            self.patients_view.refresh_data()
        elif view_name == "appointments":
            self.stacked_widget.setCurrentWidget(self.appointments_view)
            self.appointments_view.refresh_data()
        elif view_name == "settings":
            self.stacked_widget.setCurrentWidget(self.settings_view)
    
    def logout(self):
        """Log out the current user"""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to log out?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop monitoring for new appointments
            self.notification_manager.stop_monitoring()
            
            self.current_user = None
            self.current_vet = None
            self.show_login_dialog()
    
    def backup_database(self):
        """Backup the database"""
        success, result = backup_database()
        
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
    
    def show_about_dialog(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About ePetCare Vet Desktop",
            "ePetCare Vet Desktop\n"
            "Version 1.0\n\n"
            "A standalone desktop application for veterinarians to access the ePetCare system."
        )
    
    def on_new_appointment(self, appointment_id):
        """Handle new appointment notification"""
        # Refresh the views if they're visible
        if hasattr(self, 'dashboard_view'):
            self.dashboard_view.refresh_data()
        
        if hasattr(self, 'appointments_view'):
            self.appointments_view.refresh_data()
    
    def closeEvent(self, event):
        """Handle the window close event"""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop monitoring for new appointments
            self.notification_manager.stop_monitoring()
            event.accept()
        else:
            event.ignore()
