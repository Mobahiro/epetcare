"""
Dashboard view for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QScrollArea, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QSize, QDateTime
from PySide6.QtGui import QFont, QIcon

from models.data_access import AppointmentDataAccess, PetDataAccess, OwnerDataAccess


class DashboardView(QWidget):
    """Dashboard view showing upcoming appointments and recent patients"""
    
    def __init__(self, user, veterinarian):
        super().__init__()
        self.user = user
        self.veterinarian = veterinarian
        self.appointment_data_access = AppointmentDataAccess()
        self.pet_data_access = PetDataAccess()
        self.owner_data_access = OwnerDataAccess()
        
        # Set dashboard property for styling
        self.setProperty("dashboard", True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Welcome message
        welcome_label = QLabel(f"Welcome, Dr. {self.veterinarian.full_name}")
        welcome_label.setProperty("header", True)
        layout.addWidget(welcome_label)
        
        # Date and time
        date_time_label = QLabel(QDateTime.currentDateTime().toString("dddd, MMMM d, yyyy"))
        date_time_label.setProperty("subheader", True)
        layout.addWidget(date_time_label)
        
        # Create a splitter for the two main sections
        splitter = QSplitter(Qt.Vertical)
        
        # Upcoming appointments section
        appointments_group = QGroupBox("Today's Appointments")
        appointments_layout = QVBoxLayout()
        
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(5)
        self.appointments_table.setHorizontalHeaderLabels(["Time", "Pet", "Owner", "Reason", "Status"])
        self.appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointments_table.setAlternatingRowColors(True)
        
        appointments_layout.addWidget(self.appointments_table)
        appointments_group.setLayout(appointments_layout)
        splitter.addWidget(appointments_group)
        
        # Quick actions section
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()
        
        self.new_appointment_button = QPushButton("New Appointment")
        self.new_appointment_button.setMinimumHeight(50)
        self.new_appointment_button.setIcon(QIcon("resources/appointment-icon.png"))
        actions_layout.addWidget(self.new_appointment_button)
        
        self.search_patient_button = QPushButton("Search Patient")
        self.search_patient_button.setMinimumHeight(50)
        self.search_patient_button.setIcon(QIcon("resources/search-icon.png"))
        actions_layout.addWidget(self.search_patient_button)
        
        self.view_schedule_button = QPushButton("View Schedule")
        self.view_schedule_button.setMinimumHeight(50)
        self.view_schedule_button.setIcon(QIcon("resources/calendar-icon.png"))
        actions_layout.addWidget(self.view_schedule_button)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Recent patients section
        patients_group = QGroupBox("Recent Patients")
        patients_layout = QVBoxLayout()
        
        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(4)
        self.patients_table.setHorizontalHeaderLabels(["Pet Name", "Species", "Owner", "Last Visit"])
        self.patients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.patients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.patients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.patients_table.setAlternatingRowColors(True)
        
        patients_layout.addWidget(self.patients_table)
        patients_group.setLayout(patients_layout)
        splitter.addWidget(patients_group)
        
        # Add the splitter to the layout
        layout.addWidget(splitter)
        
        # Connect signals
        self.new_appointment_button.clicked.connect(self.new_appointment)
        self.search_patient_button.clicked.connect(self.search_patient)
        self.view_schedule_button.clicked.connect(self.view_schedule)
        
        # Load data
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh the data displayed in the dashboard"""
        self.load_appointments()
        self.load_recent_patients()
    
    def load_appointments(self):
        """Load today's appointments"""
        appointments = self.appointment_data_access.get_upcoming(days=1)
        
        self.appointments_table.setRowCount(0)
        
        for appointment in appointments:
            row_position = self.appointments_table.rowCount()
            self.appointments_table.insertRow(row_position)
            
            # Time
            time_item = QTableWidgetItem(appointment.date_time.strftime("%H:%M"))
            self.appointments_table.setItem(row_position, 0, time_item)
            
            # Pet
            pet_item = QTableWidgetItem(appointment.pet.name if appointment.pet else "")
            self.appointments_table.setItem(row_position, 1, pet_item)
            
            # Owner
            owner_name = ""
            if appointment.pet and hasattr(appointment.pet, 'owner') and appointment.pet.owner:
                owner_name = appointment.pet.owner.full_name
            owner_item = QTableWidgetItem(owner_name)
            self.appointments_table.setItem(row_position, 2, owner_item)
            
            # Reason
            reason_item = QTableWidgetItem(appointment.reason)
            self.appointments_table.setItem(row_position, 3, reason_item)
            
            # Status
            status_item = QTableWidgetItem(appointment.status.capitalize())
            self.appointments_table.setItem(row_position, 4, status_item)
    
    def load_recent_patients(self):
        """Load recent patients"""
        # This is a simplified implementation
        # In a real app, you would query for recent visits
        pets = self.pet_data_access.search("", limit=10)
        
        self.patients_table.setRowCount(0)
        
        for pet in pets:
            row_position = self.patients_table.rowCount()
            self.patients_table.insertRow(row_position)
            
            # Pet Name
            name_item = QTableWidgetItem(pet.name)
            self.patients_table.setItem(row_position, 0, name_item)
            
            # Species
            species_item = QTableWidgetItem(pet.species.capitalize())
            self.patients_table.setItem(row_position, 1, species_item)
            
            # Owner
            owner = self.owner_data_access.get_by_id(pet.owner_id)
            owner_name = owner.full_name if owner else ""
            owner_item = QTableWidgetItem(owner_name)
            self.patients_table.setItem(row_position, 2, owner_item)
            
            # Last Visit (placeholder)
            last_visit_item = QTableWidgetItem("N/A")
            self.patients_table.setItem(row_position, 3, last_visit_item)
    
    def new_appointment(self):
        """Open the new appointment dialog"""
        # This would be implemented in a real application
        pass
    
    def search_patient(self):
        """Open the patient search dialog"""
        # This would be implemented in a real application
        pass
    
    def view_schedule(self):
        """Open the schedule view"""
        # This would be implemented in a real application
        pass
