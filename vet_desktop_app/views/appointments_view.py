"""
Appointments view for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCalendarWidget,
    QComboBox, QGroupBox, QFormLayout, QLineEdit, QTextEdit,
    QDateTimeEdit, QMessageBox, QSplitter, QDialog, QTabWidget
)
from PySide6.QtCore import Qt, QDate, QDateTime, QTimer
from PySide6.QtGui import QFont, QIcon

from datetime import datetime, timedelta
from models.data_access import (
    AppointmentDataAccess, PetDataAccess, OwnerDataAccess
)
from models.models import Appointment, AppointmentStatus
from views.delete_confirmation_dialog import DeleteConfirmationDialog


class AppointmentsView(QWidget):
    """Appointments view showing scheduled appointments"""
    
    def __init__(self, user, veterinarian):
        super().__init__()
        self.user = user
        self.veterinarian = veterinarian
        self.appointment_data_access = AppointmentDataAccess()
        self.pet_data_access = PetDataAccess()
        self.owner_data_access = OwnerDataAccess()
        
        self.current_date = QDate.currentDate()
        self.setup_ui()
        
        # Auto-refresh timer (every 15 seconds) to reflect external changes
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(15_000)
        self._refresh_timer.timeout.connect(self.refresh_data)
        self._refresh_timer.start()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Appointments")
        title_label.setProperty("header", True)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setIcon(QIcon("resources/refresh-icon.png"))
        self.refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_button)
        
        self.new_appointment_button = QPushButton("New Appointment")
        self.new_appointment_button.setIcon(QIcon("resources/appointment-icon.png"))
        self.new_appointment_button.clicked.connect(self.new_appointment)
        header_layout.addWidget(self.new_appointment_button)
        
        layout.addLayout(header_layout)
        
        # Tab widget for different appointment views
        self.tab_widget = QTabWidget()
        
        # Calendar view tab
        calendar_tab = QWidget()
        calendar_layout = QVBoxLayout(calendar_tab)
        
        # Create a splitter for the two main sections
        splitter = QSplitter(Qt.Horizontal)
        
        # Calendar section
        calendar_group = QGroupBox("Calendar")
        calendar_group_layout = QVBoxLayout()
        
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setGridVisible(True)
        self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar_widget.setSelectionMode(QCalendarWidget.SingleSelection)
        self.calendar_widget.clicked.connect(self.date_selected)
        calendar_group_layout.addWidget(self.calendar_widget)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", "")
        self.status_filter.addItem("Scheduled", "scheduled")
        self.status_filter.addItem("Completed", "completed")
        self.status_filter.addItem("Cancelled", "cancelled")
        self.status_filter.currentIndexChanged.connect(self.filter_appointments)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        self.today_button = QPushButton("Today")
        self.today_button.clicked.connect(self.go_to_today)
        filter_layout.addWidget(self.today_button)
        
        calendar_group_layout.addLayout(filter_layout)
        calendar_group.setLayout(calendar_group_layout)
        splitter.addWidget(calendar_group)
        
        # Appointments section for calendar view
        appointments_group = QGroupBox("Appointments")
        appointments_layout = QVBoxLayout()
        
        self.date_label = QLabel()
        self.date_label.setProperty("subheader", True)
        appointments_layout.addWidget(self.date_label)
        
        self.calendar_appointments_table = QTableWidget()
        self.calendar_appointments_table.setColumnCount(5)
        self.calendar_appointments_table.setHorizontalHeaderLabels(["Time", "Pet", "Owner", "Reason", "Status"])
        self.calendar_appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.calendar_appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.calendar_appointments_table.setAlternatingRowColors(True)
        self.calendar_appointments_table.itemSelectionChanged.connect(self.calendar_appointment_selected)
        appointments_layout.addWidget(self.calendar_appointments_table)
        
        # Buttons for calendar view
        calendar_buttons_layout = QHBoxLayout()
        calendar_buttons_layout.addStretch()
        
        self.calendar_edit_button = QPushButton("Edit")
        self.calendar_edit_button.clicked.connect(lambda: self.edit_appointment(self.calendar_appointments_table))
        calendar_buttons_layout.addWidget(self.calendar_edit_button)
        
        self.calendar_complete_button = QPushButton("Mark Completed")
        self.calendar_complete_button.clicked.connect(lambda: self.complete_appointment(self.calendar_appointments_table))
        calendar_buttons_layout.addWidget(self.calendar_complete_button)
        
        self.calendar_cancel_button = QPushButton("Cancel Appointment")
        self.calendar_cancel_button.clicked.connect(lambda: self.cancel_appointment(self.calendar_appointments_table))
        calendar_buttons_layout.addWidget(self.calendar_cancel_button)
        
        self.calendar_delete_button = QPushButton("Delete")
        self.calendar_delete_button.setStyleSheet("background-color: #cc0000; color: white;")
        self.calendar_delete_button.clicked.connect(lambda: self.delete_appointment(self.calendar_appointments_table))
        calendar_buttons_layout.addWidget(self.calendar_delete_button)
        
        appointments_layout.addLayout(calendar_buttons_layout)
        appointments_group.setLayout(appointments_layout)
        splitter.addWidget(appointments_group)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 700])
        
        calendar_layout.addWidget(splitter)
        self.tab_widget.addTab(calendar_tab, "Calendar View")
        
        # All appointments tab
        all_appointments_tab = QWidget()
        all_appointments_layout = QVBoxLayout(all_appointments_tab)
        
        # Filter section
        filter_group = QGroupBox("Filter")
        filter_group_layout = QHBoxLayout()
        
        filter_group_layout.addWidget(QLabel("Status:"))
        
        self.all_status_filter = QComboBox()
        self.all_status_filter.addItem("All", "")
        self.all_status_filter.addItem("Scheduled", "scheduled")
        self.all_status_filter.addItem("Completed", "completed")
        self.all_status_filter.addItem("Cancelled", "cancelled")
        self.all_status_filter.currentIndexChanged.connect(self.filter_all_appointments)
        filter_group_layout.addWidget(self.all_status_filter)
        
        filter_group_layout.addStretch()
        
        filter_group.setLayout(filter_group_layout)
        all_appointments_layout.addWidget(filter_group)
        
        # All appointments table
        self.all_appointments_table = QTableWidget()
        self.all_appointments_table.setColumnCount(6)
        self.all_appointments_table.setHorizontalHeaderLabels(["Date", "Time", "Pet", "Owner", "Reason", "Status"])
        self.all_appointments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_appointments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.all_appointments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.all_appointments_table.setAlternatingRowColors(True)
        self.all_appointments_table.itemSelectionChanged.connect(self.all_appointment_selected)
        all_appointments_layout.addWidget(self.all_appointments_table)
        
        # Buttons for all appointments
        all_buttons_layout = QHBoxLayout()
        all_buttons_layout.addStretch()
        
        self.all_edit_button = QPushButton("Edit")
        self.all_edit_button.clicked.connect(lambda: self.edit_appointment(self.all_appointments_table))
        all_buttons_layout.addWidget(self.all_edit_button)
        
        self.all_complete_button = QPushButton("Mark Completed")
        self.all_complete_button.clicked.connect(lambda: self.complete_appointment(self.all_appointments_table))
        all_buttons_layout.addWidget(self.all_complete_button)
        
        self.all_cancel_button = QPushButton("Cancel Appointment")
        self.all_cancel_button.clicked.connect(lambda: self.cancel_appointment(self.all_appointments_table))
        all_buttons_layout.addWidget(self.all_cancel_button)
        
        self.all_delete_button = QPushButton("Delete")
        self.all_delete_button.setStyleSheet("background-color: #cc0000; color: white;")
        self.all_delete_button.clicked.connect(lambda: self.delete_appointment(self.all_appointments_table))
        all_buttons_layout.addWidget(self.all_delete_button)
        
        all_appointments_layout.addLayout(all_buttons_layout)
        
        self.tab_widget.addTab(all_appointments_tab, "All Appointments")
        
        # Add tab widget to main layout
        layout.addWidget(self.tab_widget)
        
        # Initialize with today's date and load all appointments
        self.go_to_today()
        self.load_all_appointments()
        
        # Disable buttons initially
        self.calendar_edit_button.setEnabled(False)
        self.calendar_complete_button.setEnabled(False)
        self.calendar_cancel_button.setEnabled(False)
        self.calendar_delete_button.setEnabled(False)
        self.all_edit_button.setEnabled(False)
        self.all_complete_button.setEnabled(False)
        self.all_cancel_button.setEnabled(False)
        self.all_delete_button.setEnabled(False)
    
    def refresh_data(self):
        """Refresh the data displayed in the view"""
        # Preserve selection for both tables
        selected_calendar_ids = self._get_selected_ids(self.calendar_appointments_table, id_col=0)
        selected_all_ids = self._get_selected_ids(self.all_appointments_table, id_col=0)

        self.load_appointments()
        self.load_all_appointments()

        # Restore selection
        self._restore_selection(self.calendar_appointments_table, id_col=0, ids=selected_calendar_ids)
        self._restore_selection(self.all_appointments_table, id_col=0, ids=selected_all_ids)

    def _get_selected_ids(self, table_widget: QTableWidget, id_col: int = 0):
        ids = []
        for item in table_widget.selectedItems():
            if item.column() == id_col:
                ids.append(item.data(Qt.UserRole))
        return ids

    def _restore_selection(self, table_widget: QTableWidget, id_col: int = 0, ids=None):
        if not ids:
            return
        ids = set(ids)
        table_widget.clearSelection()
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, id_col)
            if item and item.data(Qt.UserRole) in ids:
                item.setSelected(True)
    
    def go_to_today(self):
        """Go to today's date"""
        self.calendar_widget.setSelectedDate(QDate.currentDate())
        self.current_date = QDate.currentDate()
        self.date_selected(self.current_date)
    
    def date_selected(self, date):
        """Handle date selection from the calendar"""
        self.current_date = date
        self.date_label.setText(date.toString("dddd, MMMM d, yyyy"))
        self.load_appointments()
    
    def filter_appointments(self):
        """Filter appointments based on status"""
        self.load_appointments()
    
    def filter_all_appointments(self):
        """Filter all appointments based on status"""
        self.load_all_appointments()
    
    def load_appointments(self):
        """Load appointments for the selected date"""
        if not self.current_date:
            return
        
        # Convert QDate to Python date
        py_date = datetime(
            self.current_date.year(),
            self.current_date.month(),
            self.current_date.day()
        )
        
        # Get all appointments filtered by vet's branch
        vet_branch = getattr(self.veterinarian, 'branch', None)
        all_appointments = self.appointment_data_access.get_all_appointments(branch=vet_branch)
        
        # Filter by date
        appointments = []
        for appointment in all_appointments:
            appt_date = appointment.date_time.date()
            if appt_date == py_date.date():
                appointments.append(appointment)
        
        # Filter by status if needed
        status_filter = self.status_filter.currentData()
        if status_filter:
            appointments = [a for a in appointments if a.status == status_filter]
        
        # Sort by time
        appointments.sort(key=lambda a: a.date_time)
        
        # Update the table
        self.calendar_appointments_table.setRowCount(0)
        
        for appointment in appointments:
            row_position = self.calendar_appointments_table.rowCount()
            self.calendar_appointments_table.insertRow(row_position)
            
            # Time
            time_item = QTableWidgetItem(appointment.date_time.strftime("%H:%M"))
            time_item.setData(Qt.UserRole, appointment.id)
            self.calendar_appointments_table.setItem(row_position, 0, time_item)
            
            # Pet
            pet_name = appointment.pet.name if appointment.pet else "Unknown"
            pet_item = QTableWidgetItem(pet_name)
            self.calendar_appointments_table.setItem(row_position, 1, pet_item)
            
            # Owner
            owner_name = "Unknown"
            if hasattr(appointment, 'pet') and appointment.pet:
                owner_name = getattr(appointment.pet, 'owner_name', "Unknown")
            owner_item = QTableWidgetItem(owner_name)
            self.calendar_appointments_table.setItem(row_position, 2, owner_item)
            
            # Reason
            reason_item = QTableWidgetItem(appointment.reason)
            self.calendar_appointments_table.setItem(row_position, 3, reason_item)
            
            # Status
            status_item = QTableWidgetItem(appointment.status.capitalize())
            self.calendar_appointments_table.setItem(row_position, 4, status_item)
    
    def load_all_appointments(self):
        """Load all appointments (filtered by vet's branch)"""
        # Get all appointments filtered by vet's branch
        vet_branch = getattr(self.veterinarian, 'branch', None)
        all_appointments = self.appointment_data_access.get_all_appointments(branch=vet_branch)
        
        # Filter by status if needed
        status_filter = self.all_status_filter.currentData()
        if status_filter:
            all_appointments = [a for a in all_appointments if a.status == status_filter]
        
        # Sort by date and time
        all_appointments.sort(key=lambda a: a.date_time, reverse=True)
        
        # Update the table
        self.all_appointments_table.setRowCount(0)
        
        for appointment in all_appointments:
            row_position = self.all_appointments_table.rowCount()
            self.all_appointments_table.insertRow(row_position)
            
            # Date
            date_item = QTableWidgetItem(appointment.date_time.strftime("%Y-%m-%d"))
            date_item.setData(Qt.UserRole, appointment.id)
            self.all_appointments_table.setItem(row_position, 0, date_item)
            
            # Time
            time_item = QTableWidgetItem(appointment.date_time.strftime("%H:%M"))
            self.all_appointments_table.setItem(row_position, 1, time_item)
            
            # Pet
            pet_name = appointment.pet.name if appointment.pet else "Unknown"
            pet_item = QTableWidgetItem(pet_name)
            self.all_appointments_table.setItem(row_position, 2, pet_item)
            
            # Owner
            owner_name = "Unknown"
            if hasattr(appointment, 'pet') and appointment.pet:
                owner_name = getattr(appointment.pet, 'owner_name', "Unknown")
            owner_item = QTableWidgetItem(owner_name)
            self.all_appointments_table.setItem(row_position, 3, owner_item)
            
            # Reason
            reason_item = QTableWidgetItem(appointment.reason)
            self.all_appointments_table.setItem(row_position, 4, reason_item)
            
            # Status
            status_item = QTableWidgetItem(appointment.status.capitalize())
            self.all_appointments_table.setItem(row_position, 5, status_item)
    
    def calendar_appointment_selected(self):
        """Handle appointment selection in calendar view"""
        selected_items = self.calendar_appointments_table.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.calendar_edit_button.setEnabled(has_selection)
        self.calendar_complete_button.setEnabled(has_selection)
        self.calendar_cancel_button.setEnabled(has_selection)
        self.calendar_delete_button.setEnabled(has_selection)
    
    def all_appointment_selected(self):
        """Handle appointment selection in all appointments view"""
        selected_items = self.all_appointments_table.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.all_edit_button.setEnabled(has_selection)
        self.all_complete_button.setEnabled(has_selection)
        self.all_cancel_button.setEnabled(has_selection)
        self.all_delete_button.setEnabled(has_selection)
    
    def new_appointment(self):
        """Create a new appointment"""
        from views.appointment_dialog import AppointmentDialog
        
        dialog = AppointmentDialog(self)
        if dialog.exec() == QDialog.Accepted:
            appointment = dialog.get_appointment()
            
            # Save the appointment
            success, result = self.appointment_data_access.create(appointment)
            
            if success:
                QMessageBox.information(self, "Success", "Appointment scheduled successfully.")
                # Refresh both views
                self.load_appointments()
                self.load_all_appointments()
            else:
                QMessageBox.warning(self, "Error", f"Failed to schedule appointment: {result}")
    
    def edit_appointment(self, table_widget):
        """Edit the selected appointment"""
        selected_items = table_widget.selectedItems()
        if not selected_items:
            return
        
        # Get the appointment ID - it's in the first column
        col_index = 0
        if table_widget == self.all_appointments_table:
            col_index = 0  # Date column has the ID in all appointments table
        else:
            col_index = 0  # Time column has the ID in calendar appointments table
            
        appointment_id = table_widget.item(selected_items[0].row(), col_index).data(Qt.UserRole)
        
        # Get the appointment
        appointment = self.appointment_data_access.get_by_id(appointment_id)
        if not appointment:
            QMessageBox.warning(self, "Error", "Appointment not found.")
            return
        
        from views.appointment_dialog import AppointmentDialog
        
        dialog = AppointmentDialog(self, appointment.pet_id if appointment.pet_id else None, appointment)
        if dialog.exec() == QDialog.Accepted:
            updated_appointment = dialog.get_appointment()
            
            # Update the appointment
            success, result = self.appointment_data_access.update(updated_appointment)
            
            if success:
                QMessageBox.information(self, "Success", "Appointment updated successfully.")
                # Refresh both views
                self.load_appointments()
                self.load_all_appointments()
            else:
                QMessageBox.warning(self, "Error", f"Failed to update appointment: {result}")
    
    def complete_appointment(self, table_widget):
        """Mark the selected appointment as completed"""
        selected_items = table_widget.selectedItems()
        if not selected_items:
            return
        
        # Get the appointment ID
        col_index = 0
        if table_widget == self.all_appointments_table:
            col_index = 0  # Date column has the ID in all appointments table
        else:
            col_index = 0  # Time column has the ID in calendar appointments table
            
        appointment_id = table_widget.item(selected_items[0].row(), col_index).data(Qt.UserRole)
        
        # Confirm with the user
        reply = QMessageBox.question(
            self,
            "Confirm Action",
            "Are you sure you want to mark this appointment as completed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Get the appointment
        appointment = self.appointment_data_access.get_by_id(appointment_id)
        if not appointment:
            QMessageBox.warning(self, "Error", "Appointment not found.")
            return
        
        # Update the status
        appointment.status = AppointmentStatus.COMPLETED.value
        success, result = self.appointment_data_access.update(appointment)
        
        if success:
            QMessageBox.information(self, "Success", "Appointment marked as completed.")
            # Refresh both views
            self.load_appointments()
            self.load_all_appointments()
        else:
            QMessageBox.warning(self, "Error", f"Failed to update appointment: {result}")
    
    def cancel_appointment(self, table_widget):
        """Cancel the selected appointment"""
        selected_items = table_widget.selectedItems()
        if not selected_items:
            return
        
        # Get the appointment ID
        col_index = 0
        if table_widget == self.all_appointments_table:
            col_index = 0  # Date column has the ID in all appointments table
        else:
            col_index = 0  # Time column has the ID in calendar appointments table
            
        appointment_id = table_widget.item(selected_items[0].row(), col_index).data(Qt.UserRole)
        
        # Confirm with the user
        reply = QMessageBox.question(
            self,
            "Confirm Action",
            "Are you sure you want to cancel this appointment?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Get the appointment
        appointment = self.appointment_data_access.get_by_id(appointment_id)
        if not appointment:
            QMessageBox.warning(self, "Error", "Appointment not found.")
            return
        
        # Update the status
        appointment.status = AppointmentStatus.CANCELLED.value
        success, result = self.appointment_data_access.update(appointment)
        
        if success:
            QMessageBox.information(self, "Success", "Appointment cancelled.")
            # Refresh both views
            self.load_appointments()
            self.load_all_appointments()
        else:
            QMessageBox.warning(self, "Error", f"Failed to update appointment: {result}")
    
    def delete_appointment(self, table_widget):
        """Delete the selected appointment"""
        selected_items = table_widget.selectedItems()
        if not selected_items:
            return
        
        # Get the appointment ID
        col_index = 0
        if table_widget == self.all_appointments_table:
            col_index = 0  # Date column has the ID in all appointments table
        else:
            col_index = 0  # Time column has the ID in calendar appointments table
            
        appointment_id = table_widget.item(selected_items[0].row(), col_index).data(Qt.UserRole)
        
        # Get the appointment
        appointment = self.appointment_data_access.get_by_id(appointment_id)
        if not appointment:
            QMessageBox.warning(self, "Error", "Appointment not found.")
            return
        
        # Show confirmation dialog
        pet_name = appointment.pet.name if appointment.pet else "Unknown"
        reason = appointment.reason
        item_name = f"{pet_name} - {reason} ({appointment.date_time.strftime('%Y-%m-%d %H:%M')})"
        
        dialog = DeleteConfirmationDialog(
            parent=self,
            item_type="appointment",
            item_name=item_name,
            item_id=appointment_id
        )
        
        if dialog.exec() == QDialog.Accepted and dialog.confirmed:
            # Delete the appointment
            success, result = self.appointment_data_access.delete(appointment_id)
            
            if success:
                QMessageBox.information(self, "Success", "Appointment deleted successfully.")
                # Refresh both views
                self.load_appointments()
                self.load_all_appointments()
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete appointment: {result}")