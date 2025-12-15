"""
Prescription Dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QDateEdit, QMessageBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from datetime import date
from models.models import Prescription


class PrescriptionDialog(QDialog):
    """Dialog for adding/editing prescriptions"""
    
    def __init__(self, parent=None, pet_id=None, prescription=None):
        super().__init__(parent)
        self.pet_id = pet_id
        self.prescription = prescription
        self.is_edit_mode = prescription is not None
        
        self.setWindowTitle("Edit Prescription" if self.is_edit_mode else "Add Prescription")
        self.setModal(True)
        self.resize(500, 450)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Edit Prescription" if self.is_edit_mode else "Add Prescription")
        title_label.setProperty("header", True)
        layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Medication Name
        self.medication_name_edit = QLineEdit()
        self.medication_name_edit.setPlaceholderText("Enter medication name")
        form_layout.addRow("Medication Name:", self.medication_name_edit)
        
        # Dosage
        self.dosage_edit = QLineEdit()
        self.dosage_edit.setPlaceholderText("e.g., 10mg twice daily")
        form_layout.addRow("Dosage:", self.dosage_edit)
        
        # Instructions
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("Enter detailed instructions for the owner")
        self.instructions_edit.setMaximumHeight(100)
        form_layout.addRow("Instructions:", self.instructions_edit)
        
        # Date Prescribed
        self.date_prescribed_edit = QDateEdit()
        self.date_prescribed_edit.setDate(QDate.currentDate())
        self.date_prescribed_edit.setCalendarPopup(True)
        form_layout.addRow("Date Prescribed:", self.date_prescribed_edit)
        
        # Duration (days)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 365)
        self.duration_spinbox.setValue(7)
        self.duration_spinbox.setSuffix(" days")
        form_layout.addRow("Duration:", self.duration_spinbox)
        
        # Active status
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)
        form_layout.addRow("Status:", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_prescription)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        """Load existing data if in edit mode"""
        if self.is_edit_mode and self.prescription:
            self.medication_name_edit.setText(self.prescription.medication_name)
            self.dosage_edit.setText(self.prescription.dosage)
            self.instructions_edit.setPlainText(self.prescription.instructions)
            self.date_prescribed_edit.setDate(QDate.fromString(
                self.prescription.date_prescribed.isoformat(), Qt.ISODate
            ))
            self.duration_spinbox.setValue(self.prescription.duration_days or 7)
            self.active_checkbox.setChecked(self.prescription.is_active)
    
    def save_prescription(self):
        """Save the prescription"""
        # Validate input
        medication_name = self.medication_name_edit.text().strip()
        dosage = self.dosage_edit.text().strip()
        instructions = self.instructions_edit.toPlainText().strip()
        
        if not medication_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a medication name.")
            self.medication_name_edit.setFocus()
            return
        
        if not dosage:
            QMessageBox.warning(self, "Validation Error", "Please enter dosage information.")
            self.dosage_edit.setFocus()
            return
        
        if not instructions:
            QMessageBox.warning(self, "Validation Error", "Please enter instructions.")
            self.instructions_edit.setFocus()
            return
        
        # Create or update prescription
        date_prescribed = self.date_prescribed_edit.date().toPython()
        duration_days = self.duration_spinbox.value()
        is_active = self.active_checkbox.isChecked()
        
        if self.is_edit_mode:
            # Update existing prescription
            self.prescription.medication_name = medication_name
            self.prescription.dosage = dosage
            self.prescription.instructions = instructions
            self.prescription.date_prescribed = date_prescribed
            self.prescription.duration_days = duration_days
            self.prescription.is_active = is_active
        else:
            # Create new prescription
            self.prescription = Prescription(
                id=0,  # Will be set by database
                pet_id=self.pet_id,
                medication_name=medication_name,
                dosage=dosage,
                instructions=instructions,
                date_prescribed=date_prescribed,
                duration_days=duration_days,
                is_active=is_active
            )
        
        self.accept()
    
    def get_prescription(self):
        """Get the prescription data"""
        return self.prescription
