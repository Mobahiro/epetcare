"""
Patients view for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QGroupBox, QTabWidget, QFormLayout, QTextEdit,
    QDateEdit, QMessageBox, QSplitter, QStackedWidget, QDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from models.data_access import (
    PetDataAccess, OwnerDataAccess, MedicalRecordDataAccess,
    PrescriptionDataAccess, AppointmentDataAccess
)
from models.models import Pet, MedicalRecord, Prescription


class PatientsView(QWidget):
    """Patients view showing pet and owner information"""
    
    def __init__(self, user, veterinarian):
        super().__init__()
        self.user = user
        self.veterinarian = veterinarian
        self.pet_data_access = PetDataAccess()
        self.owner_data_access = OwnerDataAccess()
        self.medical_record_data_access = MedicalRecordDataAccess()
        self.prescription_data_access = PrescriptionDataAccess()
        self.appointment_data_access = AppointmentDataAccess()
        
        self.current_pet = None
        self.current_owner = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Search section
        search_group = QGroupBox("Search Patients")
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by pet name, owner name, or breed...")
        self.search_input.returnPressed.connect(self.search_patients)
        search_layout.addWidget(self.search_input, 3)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_patients)
        search_layout.addWidget(self.search_button)
        
        self.species_filter = QComboBox()
        self.species_filter.addItem("All Species", "")
        self.species_filter.addItem("Dogs", "dog")
        self.species_filter.addItem("Cats", "cat")
        self.species_filter.addItem("Birds", "bird")
        self.species_filter.addItem("Rabbits", "rabbit")
        self.species_filter.addItem("Other", "other")
        self.species_filter.currentIndexChanged.connect(self.search_patients)
        search_layout.addWidget(self.species_filter)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Create a splitter for the two main sections
        splitter = QSplitter(Qt.Horizontal)
        
        # Results section
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Pet Name", "Species", "Breed", "Owner", "Sex"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.itemSelectionChanged.connect(self.pet_selected)
        
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        splitter.addWidget(results_group)
        
        # Detail section
        self.detail_widget = QStackedWidget()
        
        # Empty state widget
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_label = QLabel("Select a pet to view details")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.detail_widget.addWidget(empty_widget)
        
        # Pet details widget
        self.pet_detail_widget = QWidget()
        pet_detail_layout = QVBoxLayout(self.pet_detail_widget)
        
        # Pet info section
        pet_info_group = QGroupBox("Pet Information")
        pet_info_layout = QFormLayout()
        
        self.pet_name_label = QLabel()
        pet_info_layout.addRow("Name:", self.pet_name_label)
        
        self.pet_species_label = QLabel()
        pet_info_layout.addRow("Species:", self.pet_species_label)
        
        self.pet_breed_label = QLabel()
        pet_info_layout.addRow("Breed:", self.pet_breed_label)
        
        self.pet_sex_label = QLabel()
        pet_info_layout.addRow("Sex:", self.pet_sex_label)
        
        self.pet_birth_label = QLabel()
        pet_info_layout.addRow("Birth Date:", self.pet_birth_label)
        
        self.pet_weight_label = QLabel()
        pet_info_layout.addRow("Weight:", self.pet_weight_label)
        
        # Add buttons for pet actions
        pet_buttons_layout = QHBoxLayout()
        
        self.edit_pet_button = QPushButton("Edit Pet")
        self.edit_pet_button.clicked.connect(self.edit_pet)
        pet_buttons_layout.addWidget(self.edit_pet_button)
        
        self.delete_pet_button = QPushButton("Delete Pet")
        self.delete_pet_button.setStyleSheet("background-color: #cc0000; color: white;")
        self.delete_pet_button.clicked.connect(self.delete_pet)
        pet_buttons_layout.addWidget(self.delete_pet_button)
        
        pet_info_layout.addRow("Actions:", pet_buttons_layout)
        
        pet_info_group.setLayout(pet_info_layout)
        pet_detail_layout.addWidget(pet_info_group)
        
        # Owner info section
        owner_info_group = QGroupBox("Owner Information")
        owner_info_layout = QFormLayout()
        
        self.owner_name_label = QLabel()
        owner_info_layout.addRow("Name:", self.owner_name_label)
        
        self.owner_email_label = QLabel()
        owner_info_layout.addRow("Email:", self.owner_email_label)
        
        self.owner_phone_label = QLabel()
        owner_info_layout.addRow("Phone:", self.owner_phone_label)
        
        self.owner_address_label = QLabel()
        owner_info_layout.addRow("Address:", self.owner_address_label)
        
        owner_info_group.setLayout(owner_info_layout)
        pet_detail_layout.addWidget(owner_info_group)
        
        # Pet records tabs
        records_tabs = QTabWidget()
        
        # Medical records tab
        medical_tab = QWidget()
        medical_layout = QVBoxLayout(medical_tab)
        
        self.medical_table = QTableWidget()
        self.medical_table.setColumnCount(3)
        self.medical_table.setHorizontalHeaderLabels(["Date", "Condition", "Treatment"])
        self.medical_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.medical_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.medical_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.medical_table.setAlternatingRowColors(True)
        
        medical_layout.addWidget(self.medical_table)
        
        medical_buttons_layout = QHBoxLayout()
        self.add_medical_button = QPushButton("Add Medical Record")
        self.add_medical_button.clicked.connect(self.add_medical_record)
        medical_buttons_layout.addWidget(self.add_medical_button)
        
        self.view_medical_button = QPushButton("View Details")
        self.view_medical_button.clicked.connect(self.view_medical_record)
        medical_buttons_layout.addWidget(self.view_medical_button)
        
        medical_layout.addLayout(medical_buttons_layout)
        records_tabs.addTab(medical_tab, "Medical Records")
        
        # Prescriptions tab
        prescriptions_tab = QWidget()
        prescriptions_layout = QVBoxLayout(prescriptions_tab)
        
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(4)
        self.prescriptions_table.setHorizontalHeaderLabels(["Date", "Medication", "Dosage", "Active"])
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.prescriptions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.prescriptions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prescriptions_table.setAlternatingRowColors(True)
        
        prescriptions_layout.addWidget(self.prescriptions_table)
        
        prescriptions_buttons_layout = QHBoxLayout()
        self.add_prescription_button = QPushButton("Add Prescription")
        self.add_prescription_button.clicked.connect(self.add_prescription)
        prescriptions_buttons_layout.addWidget(self.add_prescription_button)
        
        self.view_prescription_button = QPushButton("View Details")
        self.view_prescription_button.clicked.connect(self.view_prescription)
        prescriptions_buttons_layout.addWidget(self.view_prescription_button)
        
        prescriptions_layout.addLayout(prescriptions_buttons_layout)
        records_tabs.addTab(prescriptions_tab, "Prescriptions")
        
        # Appointments tab
        appointments_tab = QWidget()
        appointments_layout = QVBoxLayout(appointments_tab)
        
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(3)
        self.appointments_table.setHorizontalHeaderLabels(["Date & Time", "Reason", "Status"])
        self.appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointments_table.setAlternatingRowColors(True)
        
        appointments_layout.addWidget(self.appointments_table)
        
        appointments_buttons_layout = QHBoxLayout()
        self.add_appointment_button = QPushButton("Schedule Appointment")
        self.add_appointment_button.clicked.connect(self.add_appointment)
        appointments_buttons_layout.addWidget(self.add_appointment_button)
        
        self.view_appointment_button = QPushButton("View Details")
        self.view_appointment_button.clicked.connect(self.view_appointment)
        appointments_buttons_layout.addWidget(self.view_appointment_button)
        
        appointments_layout.addLayout(appointments_buttons_layout)
        records_tabs.addTab(appointments_tab, "Appointments")
        
        pet_detail_layout.addWidget(records_tabs)
        
        self.detail_widget.addWidget(self.pet_detail_widget)
        splitter.addWidget(self.detail_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def refresh_data(self):
        """Refresh the data displayed in the view"""
        self.search_patients()
    
    def search_patients(self):
        """Search for patients based on the search criteria"""
        query = self.search_input.text().strip()
        species_filter = self.species_filter.currentData()
        
        # This is a simplified implementation
        # In a real app, you would apply the species filter in the query
        pets = self.pet_data_access.search(query, limit=50)
        
        if species_filter:
            pets = [pet for pet in pets if pet.species == species_filter]
        
        self.results_table.setRowCount(0)
        
        for pet in pets:
            row_position = self.results_table.rowCount()
            self.results_table.insertRow(row_position)
            
            # Pet Name
            name_item = QTableWidgetItem(pet.name)
            name_item.setData(Qt.UserRole, pet.id)
            self.results_table.setItem(row_position, 0, name_item)
            
            # Species
            species_item = QTableWidgetItem(pet.species.capitalize())
            self.results_table.setItem(row_position, 1, species_item)
            
            # Breed
            breed_item = QTableWidgetItem(pet.breed)
            self.results_table.setItem(row_position, 2, breed_item)
            
            # Owner
            owner = self.owner_data_access.get_by_id(pet.owner_id)
            owner_name = owner.full_name if owner else ""
            owner_item = QTableWidgetItem(owner_name)
            self.results_table.setItem(row_position, 3, owner_item)
            
            # Sex
            sex_item = QTableWidgetItem(pet.sex.capitalize())
            self.results_table.setItem(row_position, 4, sex_item)
    
    def pet_selected(self):
        """Handle pet selection from the results table"""
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            self.detail_widget.setCurrentIndex(0)  # Show empty state
            self.current_pet = None
            self.current_owner = None
            return
        
        # Get the pet ID from the first column
        pet_id = self.results_table.item(selected_items[0].row(), 0).data(Qt.UserRole)

        print(f"DEBUG: Selected pet ID: {pet_id}")
        
        # Load pet details
        self.current_pet = self.pet_data_access.get_by_id(pet_id)
        if not self.current_pet:
            print(f"DEBUG: No pet found for ID: {pet_id}")
            self.detail_widget.setCurrentIndex(0)  # Show empty state
            return
        
        # Load owner details
        self.current_owner = self.owner_data_access.get_by_id(self.current_pet.owner_id)
        
        # Update pet info
        self.pet_name_label.setText(self.current_pet.name)
        self.pet_species_label.setText(self.current_pet.species.capitalize())
        self.pet_breed_label.setText(self.current_pet.breed)
        self.pet_sex_label.setText(self.current_pet.sex.capitalize())
        
        birth_date = "Unknown"
        if self.current_pet.birth_date:
            birth_date = self.current_pet.birth_date.strftime("%Y-%m-%d")
        self.pet_birth_label.setText(birth_date)
        
        weight = "Unknown"
        if self.current_pet.weight_kg:
            weight = f"{self.current_pet.weight_kg} kg"
        self.pet_weight_label.setText(weight)
        
        # Update owner info
        if self.current_owner:
            self.owner_name_label.setText(self.current_owner.full_name)
            self.owner_email_label.setText(self.current_owner.email)
            self.owner_phone_label.setText(self.current_owner.phone)
            self.owner_address_label.setText(self.current_owner.address)
        else:
            self.owner_name_label.setText("Unknown")
            self.owner_email_label.setText("")
            self.owner_phone_label.setText("")
            self.owner_address_label.setText("")
        
        # Load medical records
        self.load_medical_records()
        
        # Load prescriptions
        self.load_prescriptions()
        
        # Load appointments
        self.load_appointments()
        
        # Show the pet details
        self.detail_widget.setCurrentIndex(1)
    
    def load_medical_records(self):
        """Load medical records for the current pet"""
        if not self.current_pet:
            return
        
        records = self.medical_record_data_access.get_by_pet(self.current_pet.id)
        
        self.medical_table.setRowCount(0)
        
        for record in records:
            row_position = self.medical_table.rowCount()
            self.medical_table.insertRow(row_position)
            
            # Date
            date_item = QTableWidgetItem(record.visit_date.strftime("%Y-%m-%d"))
            date_item.setData(Qt.UserRole, record.id)
            self.medical_table.setItem(row_position, 0, date_item)
            
            # Condition
            condition_item = QTableWidgetItem(record.condition)
            self.medical_table.setItem(row_position, 1, condition_item)
            
            # Treatment
            treatment_item = QTableWidgetItem(record.treatment)
            self.medical_table.setItem(row_position, 2, treatment_item)
    
    def load_prescriptions(self):
        """Load prescriptions for the current pet"""
        if not self.current_pet:
            return
        
        prescriptions = self.prescription_data_access.get_by_pet(self.current_pet.id)
        
        self.prescriptions_table.setRowCount(0)
        
        for prescription in prescriptions:
            row_position = self.prescriptions_table.rowCount()
            self.prescriptions_table.insertRow(row_position)
            
            # Date
            date_item = QTableWidgetItem(prescription.date_prescribed.strftime("%Y-%m-%d"))
            date_item.setData(Qt.UserRole, prescription.id)
            self.prescriptions_table.setItem(row_position, 0, date_item)
            
            # Medication
            medication_item = QTableWidgetItem(prescription.medication_name)
            self.prescriptions_table.setItem(row_position, 1, medication_item)
            
            # Dosage
            dosage_item = QTableWidgetItem(prescription.dosage)
            self.prescriptions_table.setItem(row_position, 2, dosage_item)
            
            # Active
            active_item = QTableWidgetItem("Yes" if prescription.is_active else "No")
            self.prescriptions_table.setItem(row_position, 3, active_item)
    
    def load_appointments(self):
        """Load appointments for the current pet"""
        if not self.current_pet:
            return
        
        appointments = self.appointment_data_access.get_by_pet(self.current_pet.id)
        
        self.appointments_table.setRowCount(0)
        
        for appointment in appointments:
            row_position = self.appointments_table.rowCount()
            self.appointments_table.insertRow(row_position)
            
            # Date & Time
            date_time_item = QTableWidgetItem(appointment.date_time.strftime("%Y-%m-%d %H:%M"))
            date_time_item.setData(Qt.UserRole, appointment.id)
            self.appointments_table.setItem(row_position, 0, date_time_item)
            
            # Reason
            reason_item = QTableWidgetItem(appointment.reason)
            self.appointments_table.setItem(row_position, 1, reason_item)
            
            # Status
            status_item = QTableWidgetItem(appointment.status.capitalize())
            self.appointments_table.setItem(row_position, 2, status_item)
    
    def add_medical_record(self):
        """Add a new medical record"""
        if not self.current_pet:
            return
        
        from views.medical_record_dialog import MedicalRecordDialog
        
        dialog = MedicalRecordDialog(self, self.current_pet.id)
        if dialog.exec() == QDialog.Accepted:
            medical_record = dialog.get_medical_record()
            
            # Save the medical record
            success, result = self.medical_record_data_access.create(medical_record)
            
            if success:
                QMessageBox.information(self, "Success", "Medical record added successfully.")
                self.load_medical_records()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", f"Failed to add medical record: {result}")
    
    def view_medical_record(self):
        """View details of a medical record"""
        if not self.current_pet:
            return
        
        selected_items = self.medical_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a medical record to view.")
            return
        
        # Get the record ID from the selected row
        row = selected_items[0].row()
        record_id_item = self.medical_table.item(row, 0)
        record_id = record_id_item.data(Qt.UserRole)
        
        # Get the medical record
        medical_record = self.medical_record_data_access.get_by_id(record_id)
        if not medical_record:
            QMessageBox.warning(self, "Error", "Medical record not found.")
            return
        
        from views.medical_record_dialog import MedicalRecordDialog
        
        dialog = MedicalRecordDialog(self, self.current_pet.id, medical_record)
        if dialog.exec() == QDialog.Accepted:
            updated_record = dialog.get_medical_record()
            
            # Update the medical record
            success, result = self.medical_record_data_access.update(updated_record)
            
            if success:
                QMessageBox.information(self, "Success", "Medical record updated successfully.")
                self.load_medical_records()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", f"Failed to update medical record: {result}")
    
    def add_prescription(self):
        """Add a new prescription"""
        if not self.current_pet:
            return
        
        from views.prescription_dialog import PrescriptionDialog
        
        dialog = PrescriptionDialog(self, self.current_pet.id)
        if dialog.exec() == QDialog.Accepted:
            prescription = dialog.get_prescription()
            
            # Save the prescription
            success, result = self.prescription_data_access.create(prescription)
            
            if success:
                QMessageBox.information(self, "Success", "Prescription added successfully.")
                self.load_prescriptions()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", f"Failed to add prescription: {result}")
    
    def view_prescription(self):
        """View details of a prescription"""
        if not self.current_pet:
            return
        
        selected_items = self.prescriptions_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a prescription to view.")
            return
        
        # Get the prescription ID from the selected row
        row = selected_items[0].row()
        prescription_id_item = self.prescriptions_table.item(row, 0)
        prescription_id = prescription_id_item.data(Qt.UserRole)
        
        # Get the prescription
        prescription = self.prescription_data_access.get_by_id(prescription_id)
        if not prescription:
            QMessageBox.warning(self, "Error", "Prescription not found.")
            return
        
        from views.prescription_dialog import PrescriptionDialog
        
        dialog = PrescriptionDialog(self, self.current_pet.id, prescription)
        if dialog.exec() == QDialog.Accepted:
            updated_prescription = dialog.get_prescription()
            
            # Update the prescription
            success, result = self.prescription_data_access.update(updated_prescription)
            
            if success:
                QMessageBox.information(self, "Success", "Prescription updated successfully.")
                self.load_prescriptions()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", f"Failed to update prescription: {result}")
    
    def add_appointment(self):
        """Add a new appointment"""
        if not self.current_pet:
            return
        
        from views.appointment_dialog import AppointmentDialog
        
        dialog = AppointmentDialog(self, self.current_pet.id)
        if dialog.exec() == QDialog.Accepted:
            appointment = dialog.get_appointment()
            
            # Save the appointment
            success, result = self.appointment_data_access.create(appointment)
            
            if success:
                QMessageBox.information(self, "Success", "Appointment scheduled successfully.")
                self.load_appointments()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", f"Failed to schedule appointment: {result}")
    
    def view_appointment(self):
        """View details of an appointment"""
        if not self.current_pet:
            return
        
        selected_items = self.appointments_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select an appointment to view.")
            return
        
        # Get the appointment ID from the selected row
        row = selected_items[0].row()
        appointment_id_item = self.appointments_table.item(row, 0)
        appointment_id = appointment_id_item.data(Qt.UserRole)
        
        # Get the appointment
        appointment = self.appointment_data_access.get_by_id(appointment_id)
        if not appointment:
            QMessageBox.warning(self, "Error", "Appointment not found.")
            return
        
        from views.appointment_dialog import AppointmentDialog
        
        dialog = AppointmentDialog(self, self.current_pet.id, appointment)
        if dialog.exec() == QDialog.Accepted:
            updated_appointment = dialog.get_appointment()
            
            # Update the appointment
            success, result = self.appointment_data_access.update(updated_appointment)
            
            if success:
                QMessageBox.information(self, "Success", "Appointment updated successfully.")
                self.load_appointments()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", f"Failed to update appointment: {result}")
        
    def edit_pet(self):
        """Edit the current pet"""
        if not self.current_pet:
            return
            
        QMessageBox.information(self, "Not Implemented", "This feature is not yet implemented.")
        
    def delete_pet(self):
        """Delete the current pet"""
        if not self.current_pet:
            return
            
        # Import the delete confirmation dialog
        from views.delete_confirmation_dialog import DeleteConfirmationDialog
        
        # Show confirmation dialog
        dialog = DeleteConfirmationDialog(
            parent=self,
            item_type="pet",
            item_name=f"{self.current_pet.name} ({self.current_pet.species}, {self.current_pet.breed})",
            item_id=self.current_pet.id
        )
        
        if dialog.exec() == QDialog.Accepted and dialog.confirmed:
            # Delete the pet
            success, result = self.pet_data_access.delete(self.current_pet.id)
            
            if success:
                QMessageBox.information(self, "Success", f"Pet '{self.current_pet.name}' deleted successfully.")
                # Clear the current pet and refresh the list
                self.current_pet = None
                self.detail_widget.setCurrentIndex(0)  # Show empty state
                self.search_patients()  # Refresh the list
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete pet: {result}")
