"""
Dashboard view for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QScrollArea, QSplitter, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QDateTime, QDate
from PySide6.QtGui import QFont, QIcon, QColor, QBrush

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
        welcome_font = QFont()
        welcome_font.setPointSize(16)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        layout.addWidget(welcome_label)
        
        # Date and time
        date_time_label = QLabel(QDateTime.currentDateTime().toString("dddd, MMMM d, yyyy"))
        date_font = QFont()
        date_font.setPointSize(12)
        date_time_label.setFont(date_font)
        layout.addWidget(date_time_label)
        
        # Quick actions section
        actions_group = QGroupBox("Quick Actions")
        actions_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        actions_layout = QGridLayout()
        actions_layout.setSpacing(10)
        
        # Create action buttons with icons
        self.new_appointment_button = self._create_action_button(
            "New Appointment", 
            QIcon.fromTheme("appointment-new", QIcon.fromTheme("calendar-new")),
            "Create a new appointment"
        )
        actions_layout.addWidget(self.new_appointment_button, 0, 0)
        
        self.search_patient_button = self._create_action_button(
            "Search Patient", 
            QIcon.fromTheme("system-search", QIcon.fromTheme("edit-find")),
            "Search for a patient"
        )
        actions_layout.addWidget(self.search_patient_button, 0, 1)
        
        self.view_schedule_button = self._create_action_button(
            "View Schedule", 
            QIcon.fromTheme("x-office-calendar", QIcon.fromTheme("view-calendar")),
            "View your appointment schedule"
        )
        actions_layout.addWidget(self.view_schedule_button, 0, 2)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Create a splitter for the two main sections
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        # Today's appointments section
        appointments_group = QGroupBox("Today's Appointments")
        appointments_layout = QVBoxLayout()
        
        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(5)
        self.appointments_table.setHorizontalHeaderLabels(["Time", "Pet", "Owner", "Reason", "Status"])
        self.appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointments_table.setAlternatingRowColors(True)
        self.appointments_table.setMinimumHeight(150)
        
        appointments_layout.addWidget(self.appointments_table)
        appointments_group.setLayout(appointments_layout)
        splitter.addWidget(appointments_group)
        
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
        self.patients_table.setMinimumHeight(150)
        
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
    
    def _create_action_button(self, text, icon, tooltip=None):
        """Helper method to create a styled action button"""
        button = QPushButton(text)
        button.setIcon(icon)
        button.setIconSize(QSize(32, 32))
        button.setMinimumHeight(60)
        button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        if tooltip:
            button.setToolTip(tooltip)
        return button
    
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
            
            # Color code the status
            if appointment.status == "scheduled":
                status_item.setBackground(QBrush(QColor("#3498db")))  # Blue
                status_item.setForeground(QBrush(QColor("white")))
            elif appointment.status == "completed":
                status_item.setBackground(QBrush(QColor("#2ecc71")))  # Green
                status_item.setForeground(QBrush(QColor("white")))
            elif appointment.status == "cancelled":
                status_item.setBackground(QBrush(QColor("#e74c3c")))  # Red
                status_item.setForeground(QBrush(QColor("white")))
            
            self.appointments_table.setItem(row_position, 4, status_item)
        
        # If no appointments, add a placeholder row
        if self.appointments_table.rowCount() == 0:
            self.appointments_table.insertRow(0)
            no_appt_item = QTableWidgetItem("No appointments scheduled for today")
            no_appt_item.setTextAlignment(Qt.AlignCenter)
            self.appointments_table.setSpan(0, 0, 1, 5)
            self.appointments_table.setItem(0, 0, no_appt_item)
    
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
        
        # If no patients, add a placeholder row
        if self.patients_table.rowCount() == 0:
            self.patients_table.insertRow(0)
            no_patients_item = QTableWidgetItem("No recent patients")
            no_patients_item.setTextAlignment(Qt.AlignCenter)
            self.patients_table.setSpan(0, 0, 1, 4)
            self.patients_table.setItem(0, 0, no_patients_item)
    
    def new_appointment(self):
        """Open the new appointment dialog"""
        from PySide6.QtWidgets import QMessageBox, QDialog
        try:
            # Lazy import to avoid circulars in some packaging modes
            from views.appointment_dialog import AppointmentDialog
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Unable to open appointment dialog: {e}")
            return

        dialog = AppointmentDialog(self)
        if dialog.exec() == QDialog.Accepted:
            appt = dialog.get_appointment()
            success, result = self.appointment_data_access.create(appt)
            if success:
                QMessageBox.information(self, "Success", "Appointment scheduled successfully.")
                # Refresh dashboard data and optionally jump to schedule view
                self.refresh_data()
                main_window = self.window()
                if main_window and hasattr(main_window, 'show_view'):
                    main_window.show_view("appointments")
            else:
                QMessageBox.warning(self, "Error", f"Failed to schedule appointment: {result}")
    
    def search_patient(self):
        """Open the patient search dialog"""
        # Switch to patients view on the top-level window
        main_window = self.window()
        if main_window and hasattr(main_window, 'show_view'):
            main_window.show_view("patients")
    
    def view_schedule(self):
        """Open the schedule view"""
        # Switch to appointments view on the top-level window
        main_window = self.window()
        if main_window and hasattr(main_window, 'show_view'):
            main_window.show_view("appointments")