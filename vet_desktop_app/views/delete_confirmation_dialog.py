"""
Delete confirmation dialog for the ePetCare Vet Desktop application.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
import logging

logger = logging.getLogger('epetcare')

class DeleteConfirmationDialog(QDialog):
    """Dialog to confirm deletion of an item"""
    
    def __init__(self, parent=None, item_type="item", item_name="", item_id=None):
        """Initialize the delete confirmation dialog"""
        super().__init__(parent)
        
        self.item_type = item_type
        self.item_name = item_name
        self.item_id = item_id
        self.confirmed = False
        
        self.setWindowTitle(f"Delete {item_type.title()}")
        self.setMinimumWidth(400)
        
        # Set up the layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Warning icon and message
        message_layout = QHBoxLayout()
        
        # Warning icon
        try:
            warning_icon = QIcon.fromTheme("dialog-warning")
            if warning_icon.isNull():
                # Fallback to system warning icon
                from PySide6.QtWidgets import QStyle
                warning_icon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
                
            icon_label = QLabel()
            icon_label.setPixmap(warning_icon.pixmap(48, 48))
            message_layout.addWidget(icon_label)
        except Exception as e:
            logger.warning(f"Could not load warning icon: {e}")
        
        # Warning message
        message_label = QLabel(f"Are you sure you want to delete this {item_type}?")
        message_label.setWordWrap(True)
        message_layout.addWidget(message_label, 1)
        
        layout.addLayout(message_layout)
        
        # Item details
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.StyledPanel)
        details_frame.setFrameShadow(QFrame.Sunken)
        details_layout = QVBoxLayout(details_frame)
        
        # Item name
        name_label = QLabel(f"<b>Name:</b> {item_name}")
        name_label.setTextFormat(Qt.RichText)
        details_layout.addWidget(name_label)
        
        # Item ID
        if item_id is not None:
            id_label = QLabel(f"<b>ID:</b> {item_id}")
            id_label.setTextFormat(Qt.RichText)
            details_layout.addWidget(id_label)
        
        layout.addWidget(details_frame)
        
        # Warning message
        warning_label = QLabel(
            "<b>Warning:</b> This action cannot be undone. "
            f"The {item_type} will be permanently deleted."
        )
        warning_label.setTextFormat(Qt.RichText)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #cc0000;")
        layout.addWidget(warning_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet("background-color: #cc0000; color: white;")
        delete_button.clicked.connect(self.confirm_delete)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
    
    def confirm_delete(self):
        """Confirm the deletion"""
        self.confirmed = True
        self.accept()
