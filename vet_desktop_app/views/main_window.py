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
import sys
import os
import importlib.util
import logging

logger = logging.getLogger('epetcare')

# Special handling for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    logger.debug("main_window.py: Using special import handling for frozen app")
    
    try:
        # Try normal imports first
        from views.login_dialog import LoginDialog
        from views.dashboard_view import DashboardView
        from views.patients_view import PatientsView
        from views.appointments_view import AppointmentsView
        from views.settings_view import SettingsView
        from utils.database import backup_database
        from utils.notification_manager import NotificationManager
        logger.debug("Successfully imported modules in main_window.py")
    except ImportError as e:
        logger.error(f"Import error in main_window.py: {e}")
        
        # Get the base directory
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import directly from files
        try:
            # Import login_dialog
            login_dialog_path = os.path.join(base_dir, 'views', 'login_dialog.py')
            if os.path.exists(login_dialog_path):
                spec = importlib.util.spec_from_file_location("views.login_dialog", login_dialog_path)
                login_dialog_module = importlib.util.module_from_spec(spec)
                sys.modules['views.login_dialog'] = login_dialog_module
                spec.loader.exec_module(login_dialog_module)
                LoginDialog = login_dialog_module.LoginDialog
                logger.debug(f"Imported LoginDialog from {login_dialog_path}")
            else:
                logger.error(f"login_dialog.py not found at {login_dialog_path}")
                
            # Import dashboard_view
            dashboard_view_path = os.path.join(base_dir, 'views', 'dashboard_view.py')
            if os.path.exists(dashboard_view_path):
                spec = importlib.util.spec_from_file_location("views.dashboard_view", dashboard_view_path)
                dashboard_view_module = importlib.util.module_from_spec(spec)
                sys.modules['views.dashboard_view'] = dashboard_view_module
                spec.loader.exec_module(dashboard_view_module)
                DashboardView = dashboard_view_module.DashboardView
                logger.debug(f"Imported DashboardView from {dashboard_view_path}")
            else:
                logger.error(f"dashboard_view.py not found at {dashboard_view_path}")
                
            # Import patients_view
            patients_view_path = os.path.join(base_dir, 'views', 'patients_view.py')
            if os.path.exists(patients_view_path):
                spec = importlib.util.spec_from_file_location("views.patients_view", patients_view_path)
                patients_view_module = importlib.util.module_from_spec(spec)
                sys.modules['views.patients_view'] = patients_view_module
                spec.loader.exec_module(patients_view_module)
                PatientsView = patients_view_module.PatientsView
                logger.debug(f"Imported PatientsView from {patients_view_path}")
            else:
                logger.error(f"patients_view.py not found at {patients_view_path}")
                
            # Import appointments_view
            appointments_view_path = os.path.join(base_dir, 'views', 'appointments_view.py')
            if os.path.exists(appointments_view_path):
                spec = importlib.util.spec_from_file_location("views.appointments_view", appointments_view_path)
                appointments_view_module = importlib.util.module_from_spec(spec)
                sys.modules['views.appointments_view'] = appointments_view_module
                spec.loader.exec_module(appointments_view_module)
                AppointmentsView = appointments_view_module.AppointmentsView
                logger.debug(f"Imported AppointmentsView from {appointments_view_path}")
            else:
                logger.error(f"appointments_view.py not found at {appointments_view_path}")
                
            # Import settings_view
            settings_view_path = os.path.join(base_dir, 'views', 'settings_view.py')
            if os.path.exists(settings_view_path):
                spec = importlib.util.spec_from_file_location("views.settings_view", settings_view_path)
                settings_view_module = importlib.util.module_from_spec(spec)
                sys.modules['views.settings_view'] = settings_view_module
                spec.loader.exec_module(settings_view_module)
                SettingsView = settings_view_module.SettingsView
                logger.debug(f"Imported SettingsView from {settings_view_path}")
            else:
                logger.error(f"settings_view.py not found at {settings_view_path}")
                
            # Import utils.database
            from utils.database import backup_database
            
            # Import utils.notification_manager
            from utils.notification_manager import NotificationManager
            
        except Exception as e:
            logger.error(f"Error importing modules in main_window.py: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
else:
    # Running as a normal Python script
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
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Get resource path
        resource_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
        
        # Use system icons if available, otherwise try to load from resources
        # Dashboard action
        dashboard_icon = QIcon.fromTheme("dashboard", QIcon(os.path.join(resource_path, 'dashboard-icon.png')))
        if dashboard_icon.isNull():
            dashboard_icon = QIcon.fromTheme("view-grid", QIcon.fromTheme("applications-system"))
        dashboard_action = QAction(dashboard_icon, "Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.show_view("dashboard"))
        dashboard_action.setStatusTip("View dashboard")
        self.toolbar.addAction(dashboard_action)
        
        # Patients action
        patients_icon = QIcon.fromTheme("contact-new", QIcon(os.path.join(resource_path, 'patients-icon.png')))
        if patients_icon.isNull():
            patients_icon = QIcon.fromTheme("system-users", QIcon.fromTheme("user-info"))
        patients_action = QAction(patients_icon, "Patients", self)
        patients_action.triggered.connect(lambda: self.show_view("patients"))
        patients_action.setStatusTip("Manage patients")
        self.toolbar.addAction(patients_action)
        
        # Appointments action
        appointments_icon = QIcon.fromTheme("x-office-calendar", QIcon(os.path.join(resource_path, 'appointments-icon.png')))
        if appointments_icon.isNull():
            appointments_icon = QIcon.fromTheme("appointment-new", QIcon.fromTheme("office-calendar"))
        appointments_action = QAction(appointments_icon, "Appointments", self)
        appointments_action.triggered.connect(lambda: self.show_view("appointments"))
        appointments_action.setStatusTip("Manage appointments")
        self.toolbar.addAction(appointments_action)
        
        self.toolbar.addSeparator()
        
        # Settings action
        settings_icon = QIcon.fromTheme("preferences-system", QIcon(os.path.join(resource_path, 'settings-icon.png')))
        if settings_icon.isNull():
            settings_icon = QIcon.fromTheme("configure", QIcon.fromTheme("applications-system"))
        settings_action = QAction(settings_icon, "Settings", self)
        settings_action.triggered.connect(lambda: self.show_view("settings"))
        settings_action.setStatusTip("Configure application settings")
        self.toolbar.addAction(settings_action)
        
        # Backup action
        backup_icon = QIcon.fromTheme("document-save", QIcon(os.path.join(resource_path, 'backup-icon.png')))
        if backup_icon.isNull():
            backup_icon = QIcon.fromTheme("media-floppy", QIcon.fromTheme("drive-harddisk"))
        backup_action = QAction(backup_icon, "Backup", self)
        backup_action.triggered.connect(self.backup_database)
        backup_action.setStatusTip("Backup the database")
        self.toolbar.addAction(backup_action)
        
        # Logout action
        logout_icon = QIcon.fromTheme("system-log-out", QIcon(os.path.join(resource_path, 'logout-icon.png')))
        if logout_icon.isNull():
            logout_icon = QIcon.fromTheme("application-exit", QIcon.fromTheme("dialog-close"))
        logout_action = QAction(logout_icon, "Logout", self)
        logout_action.triggered.connect(self.logout)
        logout_action.setStatusTip("Log out of the application")
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
            
            # Set window title with user name
            self.setWindowTitle(f"ePetCare Vet Portal - {self.current_user.username}")
        else:
            # Exit if login is cancelled and no user is logged in
            if not self.current_user:
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
            
            # Clear current user data
            self.current_user = None
            self.current_vet = None
            
            # Reset UI state
            self.central_widget.setCurrentIndex(0)
            
            # Show login dialog
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
