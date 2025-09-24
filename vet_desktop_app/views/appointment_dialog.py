"""
Appointment Dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QDateTimeEdit, QMessageBox, 
    QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont

from datetime import datetime, timedelta
from models.models import Appointment, AppointmentStatus


class AppointmentDialog(QDialog):
    """Dialog for adding/editing appointments"""
    
    def __init__(self, parent=None, pet_id=None, appointment=None):
        super().__init__(parent)
        self.pet_id = pet_id
        self.appointment = appointment
        self.is_edit_mode = appointment is not None
        
        self.setWindowTitle("Edit Appointment" if self.is_edit_mode else "Schedule Appointment")
        self.setModal(True)
        self.resize(500, 450)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Edit Appointment" if self.is_edit_mode else "Schedule Appointment")
        title_label.setProperty("header", True)
        layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Appointment Date & Time
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        form_layout.addRow("Date & Time:", self.datetime_edit)
        
        # Duration (minutes)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(15, 240)
        self.duration_spinbox.setValue(30)
        self.duration_spinbox.setSuffix(" minutes")
        form_layout.addRow("Duration:", self.duration_spinbox)
        
        # Appointment Type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Checkup",
            "Vaccination", 
            "Surgery",
            "Emergency",
            "Follow-up",
            "Consultation",
            "Other"
        ])
        form_layout.addRow("Type:", self.type_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Scheduled",
            "Confirmed", 
            "In Progress",
            "Completed",
            "Cancelled",
            "No Show"
        ])
        form_layout.addRow("Status:", self.status_combo)
        
        # Reason/Notes
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("Enter reason for appointment or notes")
        self.reason_edit.setMaximumHeight(100)
        form_layout.addRow("Reason/Notes:", self.reason_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_appointment)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        """Load existing data if in edit mode"""
        if self.is_edit_mode and self.appointment:
            # Convert datetime string to QDateTime
            appointment_datetime = QDateTime.fromString(
                self.appointment.date_time.isoformat(), Qt.ISODate
            )
            self.datetime_edit.setDateTime(appointment_datetime)
            self.duration_spinbox.setValue(self.appointment.duration_minutes)
            
            # Set appointment type
            type_index = self.type_combo.findText(self.appointment.appointment_type)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
            
            # Set status
            status_index = self.status_combo.findText(self.appointment.status.value.title())
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)
            
            self.reason_edit.setPlainText(self.appointment.reason or "")
    
    def save_appointment(self):
        """Save the appointment"""
        # Validate input
        reason = self.reason_edit.toPlainText().strip()
        
        # Get appointment datetime
        appointment_datetime = self.datetime_edit.dateTime().toPython()
        
        # Check if appointment is in the past (only for new appointments)
        if not self.is_edit_mode and appointment_datetime < datetime.now():
            QMessageBox.warning(self, "Validation Error", "Appointment cannot be scheduled in the past.")
            self.datetime_edit.setFocus()
            return
        
        # Create or update appointment
        duration_minutes = self.duration_spinbox.value()
        appointment_type = self.type_combo.currentText()
        status_text = self.status_combo.currentText().lower().replace(" ", "_")
        
        # Convert status text to enum
        try:
            status = AppointmentStatus(status_text)
        except ValueError:
            status = AppointmentStatus.SCHEDULED
        
        if self.is_edit_mode:
            # Update existing appointment
            self.appointment.date_time = appointment_datetime
            self.appointment.reason = reason
            self.appointment.status = status
        else:
            # Create new appointment
            self.appointment = Appointment(
                id=0,  # Will be set by database
                pet_id=self.pet_id,
                date_time=appointment_datetime,
                reason=reason,
                notes="",
                status=status
            )
        
        self.accept()
    
    def get_appointment(self):
        """Get the appointment data"""
        return self.appointment
