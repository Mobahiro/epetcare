"""
Notification manager for the ePetCare Vet Desktop application.
"""

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QAction, QIcon
from datetime import datetime, timedelta

from models.data_access import AppointmentDataAccess


class NotificationManager(QObject):
    """Notification manager for the application"""
    
    new_appointment_signal = Signal(int)  # Emits appointment ID when a new appointment is detected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.appointment_data_access = AppointmentDataAccess()
        self.known_appointment_ids = set()
        self.check_interval = 60000  # 60 seconds by default
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_new_appointments)
        self.system_tray = None
        self.setup_system_tray()
    
    def setup_system_tray(self):
        """Set up system tray icon if supported"""
        # Create a default icon for the system tray
        default_icon = QIcon()
        default_icon.addFile("resources/app-icon.png")
        
        # If no icon file exists, create a simple icon
        if default_icon.isNull():
            # Create a 16x16 pixel icon with a blue background
            from PySide6.QtGui import QPixmap, QPainter, QColor
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(0, 102, 204))  # Blue color
            default_icon = QIcon(pixmap)
        
        if QSystemTrayIcon.isSystemTrayAvailable():
            try:
                self.system_tray = QSystemTrayIcon(self.parent())
                self.system_tray.setIcon(default_icon)
                self.system_tray.setToolTip("ePetCare Vet Desktop")
                
                # Create tray menu
                tray_menu = QMenu()
                show_action = QAction("Show", self)
                show_action.triggered.connect(self.show_main_window)
                tray_menu.addAction(show_action)
                
                tray_menu.addSeparator()
                
                quit_action = QAction("Quit", self)
                quit_action.triggered.connect(self.quit_application)
                tray_menu.addAction(quit_action)
                
                self.system_tray.setContextMenu(tray_menu)
                self.system_tray.show()
            except Exception as e:
                print(f"Failed to set up system tray: {e}")
                self.system_tray = None
    
    def start_monitoring(self):
        """Start monitoring for new appointments"""
        # First, load all existing appointment IDs
        self.load_existing_appointments()
        
        # Start the timer
        self.timer.start(self.check_interval)
    
    def stop_monitoring(self):
        """Stop monitoring for new appointments"""
        self.timer.stop()
    
    def load_existing_appointments(self):
        """Load all existing appointment IDs"""
        appointments = self.appointment_data_access.get_all_appointments()
        self.known_appointment_ids = {appointment.id for appointment in appointments}
    
    def check_for_new_appointments(self):
        """Check for new appointments"""
        current_appointments = self.appointment_data_access.get_all_appointments()
        current_ids = {appointment.id for appointment in current_appointments}
        
        # Find new appointments
        new_appointment_ids = current_ids - self.known_appointment_ids
        
        if new_appointment_ids:
            # Update known appointments
            self.known_appointment_ids = current_ids
            
            # Notify about new appointments
            for appointment_id in new_appointment_ids:
                self.new_appointment_signal.emit(appointment_id)
                
                # Find the appointment details
                for appointment in current_appointments:
                    if appointment.id == appointment_id:
                        self.show_notification(
                            "New Appointment",
                            f"New appointment scheduled for {appointment.pet.name} on "
                            f"{appointment.date_time.strftime('%Y-%m-%d %H:%M')}"
                        )
                        break
    
    def show_notification(self, title, message):
        """Show a notification"""
        try:
            if self.system_tray and QSystemTrayIcon.isSystemTrayAvailable():
                self.system_tray.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.Information,
                    5000  # Show for 5 seconds
                )
            else:
                # If system tray is not available, show a message box instead
                print(f"Notification: {title} - {message}")
                # Don't block the UI with a message box
                # QMessageBox.information(None, title, message)
        except Exception as e:
            print(f"Failed to show notification: {e}")
    
    def show_main_window(self):
        """Show the main window"""
        if self.parent():
            self.parent().show()
            self.parent().activateWindow()
    
    def quit_application(self):
        """Quit the application"""
        if self.parent():
            self.parent().close()
