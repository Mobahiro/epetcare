"""
Medical Record Dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from datetime import date
from models.models import MedicalRecord


class MedicalRecordDialog(QDialog):
    """Dialog for adding/editing medical records"""
    
    def __init__(self, parent=None, pet_id=None, medical_record=None):
        super().__init__(parent)
        self.pet_id = pet_id
        self.medical_record = medical_record
        self.is_edit_mode = medical_record is not None
        
        self.setWindowTitle("Edit Medical Record" if self.is_edit_mode else "Add Medical Record")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Edit Medical Record" if self.is_edit_mode else "Add Medical Record")
        title_label.setProperty("header", True)
        layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Visit Date
        self.visit_date_edit = QDateEdit()
        self.visit_date_edit.setDate(QDate.currentDate())
        self.visit_date_edit.setCalendarPopup(True)
        form_layout.addRow("Visit Date:", self.visit_date_edit)
        
        # Condition
        self.condition_edit = QLineEdit()
        self.condition_edit.setPlaceholderText("Enter the medical condition")
        form_layout.addRow("Condition:", self.condition_edit)
        
        # Treatment
        self.treatment_edit = QTextEdit()
        self.treatment_edit.setPlaceholderText("Enter treatment details")
        self.treatment_edit.setMaximumHeight(100)
        form_layout.addRow("Treatment:", self.treatment_edit)
        
        # Vet Notes
        self.vet_notes_edit = QTextEdit()
        self.vet_notes_edit.setPlaceholderText("Enter veterinary notes")
        self.vet_notes_edit.setMaximumHeight(100)
        form_layout.addRow("Vet Notes:", self.vet_notes_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_record)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        """Load existing data if in edit mode"""
        if self.is_edit_mode and self.medical_record:
            self.visit_date_edit.setDate(QDate.fromString(
                self.medical_record.visit_date.isoformat(), Qt.ISODate
            ))
            self.condition_edit.setText(self.medical_record.condition)
            self.treatment_edit.setPlainText(self.medical_record.treatment)
            self.vet_notes_edit.setPlainText(self.medical_record.vet_notes)
    
    def save_record(self):
        """Save the medical record"""
        # Validate input
        condition = self.condition_edit.text().strip()
        treatment = self.treatment_edit.toPlainText().strip()
        vet_notes = self.vet_notes_edit.toPlainText().strip()
        
        if not condition:
            QMessageBox.warning(self, "Validation Error", "Please enter a condition.")
            self.condition_edit.setFocus()
            return
        
        if not treatment:
            QMessageBox.warning(self, "Validation Error", "Please enter treatment details.")
            self.treatment_edit.setFocus()
            return
        
        # Create or update medical record
        visit_date = self.visit_date_edit.date().toPython()
        
        if self.is_edit_mode:
            # Update existing record
            self.medical_record.visit_date = visit_date
            self.medical_record.condition = condition
            self.medical_record.treatment = treatment
            self.medical_record.vet_notes = vet_notes
        else:
            # Create new record
            self.medical_record = MedicalRecord(
                id=0,  # Will be set by database
                pet_id=self.pet_id,
                visit_date=visit_date,
                condition=condition,
                treatment=treatment,
                vet_notes=vet_notes
            )
        
        self.accept()
    
    def get_medical_record(self):
        """Get the medical record data"""
        return self.medical_record
