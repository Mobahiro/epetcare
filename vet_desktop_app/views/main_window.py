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
        from utils.pg_backup import backup_postgres_data
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

            # Import utils.pg_backup
            from utils.pg_backup import backup_postgres_data

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
    from utils.pg_backup import backup_postgres_data
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

        # Debug log the resource path
        logger.info(f"Looking for icons in: {resource_path}")
        if os.path.exists(resource_path):
            logger.info(f"Resource directory contents: {os.listdir(resource_path)}")
        else:
            os.makedirs(resource_path, exist_ok=True)
            logger.warning(f"Resources directory didn't exist, created at: {resource_path}")

        # Helper function to ensure we have a valid icon
        def get_icon(icon_name, fallback_char):
            from PySide6.QtGui import QPixmap

            icon_path = os.path.join(resource_path, icon_name)
            logger.info(f"Trying to load icon: {icon_path}")

            # Try to load from file
            if os.path.exists(icon_path):
                logger.info(f"Icon file exists: {icon_path}")
                try:
                    # Try loading with QPixmap first (often more reliable)
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        logger.info(f"Successfully loaded icon via QPixmap: {icon_name}")
                        icon = QIcon(pixmap)
                        return icon
                    else:
                        logger.warning(f"QPixmap is null for: {icon_path}")

                    # Fall back to direct QIcon loading
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        logger.info(f"Successfully loaded icon via QIcon: {icon_name}")
                        return icon
                    else:
                        logger.warning(f"Both QPixmap and QIcon failed to load: {icon_path}")
                except Exception as e:
                    logger.error(f"Error loading icon {icon_path}: {e}")
            else:
                logger.warning(f"Icon file does not exist: {icon_path}")

            # If icon couldn't be loaded from file, try system theme
            theme_names = [icon_name.split('-')[0], "application", "app"]
            for theme_name in theme_names:
                theme_icon = QIcon.fromTheme(theme_name)
                if not theme_icon.isNull():
                    return theme_icon

            # If we still don't have an icon, try to generate one on the fly
            logger.warning(f"Icon not found: {icon_name}, creating temporary icon")
            try:
                from PIL import Image, ImageDraw
                import tempfile

                # Create a temporary icon file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_path = temp_file.name
                temp_file.close()

                # Get color based on fallback_char
                color_map = {
                    'D': (0, 120, 212),   # Blue - Dashboard
                    'P': (46, 125, 50),    # Green - Patients
                    'A': (211, 47, 47),    # Red - Appointments
                    'S': (123, 31, 162),   # Purple - Settings
                    'B': (255, 143, 0),    # Orange - Backup
                    'L': (66, 66, 66),     # Gray - Logout
                }
                color = color_map.get(fallback_char, (100, 100, 100))

                # Create a simple colored square with text
                img = Image.new('RGB', (64, 64), color)
                draw = ImageDraw.Draw(img)
                # Draw a white square in the middle
                draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
                # Save the image
                img.save(temp_path)

                # Load the icon from the temp file
                icon = QIcon(temp_path)
                return icon
            except Exception as e:
                logger.error(f"Failed to create icon: {e}")

            # Return even if null (will be handled by QAction)
            return icon

        # Create colored icons for all actions
        action_specs = [
            ('dashboard-icon.png', 'D', "Dashboard", lambda: self.show_view("dashboard"), "View dashboard"),
            ('patients-icon.png', 'P', "Patients", lambda: self.show_view("patients"), "Manage patients"),
            ('appointments-icon.png', 'A', "Appointments", lambda: self.show_view("appointments"), "Manage appointments"),
            None,  # Separator
            ('settings-icon.png', 'S', "Settings", lambda: self.show_view("settings"), "Configure application settings"),
            ('backup-icon.png', 'B', "Backup", self.backup_database, "Backup the database"),
            ('logout-icon.png', 'L', "Logout", self.logout, "Log out of the application")
        ]

        # Add all actions to the toolbar
        for spec in action_specs:
            if spec is None:
                # Add separator
                self.toolbar.addSeparator()
                continue

            icon_file, letter, label, callback, status_tip = spec

            # Get icon with fallback
            icon = get_icon(icon_file, letter)

            # Create the action
            action = QAction(icon, label, self)
            action.triggered.connect(callback)
            action.setStatusTip(status_tip)

            # Add to toolbar
            self.toolbar.addAction(action)

            # Log the result
            logger.info(f"Added action {label} to toolbar with icon from {icon_file}")

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
        """Backup the PostgreSQL database"""
        success, result = backup_postgres_data()

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
