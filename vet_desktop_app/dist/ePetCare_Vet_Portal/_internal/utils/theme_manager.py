"""
Theme manager for the ePetCare Vet Desktop application.
"""

import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from utils.config import get_config_value

def apply_theme(app=None):
    """
    Apply the selected theme to the application.
    
    Args:
        app: QApplication instance (uses QApplication.instance() if None)
    """
    if app is None:
        app = QApplication.instance()
        if app is None:
            return False
    
    theme = get_config_value('ui', 'theme', 'light')
    
    if theme == 'dark':
        return apply_dark_theme(app)
    else:
        return apply_light_theme(app)

def apply_light_theme(app):
    """Apply light theme to the application"""
    import sys
    # Reset to default palette
    app.setPalette(QPalette())
    
    # Try to load stylesheet - handle both dev and frozen (PyInstaller) modes
    possible_paths = []
    
    # Path for development mode
    resource_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
    possible_paths.append(os.path.join(resource_path, 'light_style.qss'))
    
    # Path for PyInstaller frozen app
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(sys.executable)
        possible_paths.append(os.path.join(base_dir, 'resources', 'light_style.qss'))
        possible_paths.append(os.path.join(base_dir, 'light_style.qss'))
    
    # Try all possible paths
    for style_path in possible_paths:
        if os.path.exists(style_path):
            try:
                with open(style_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
                print(f"Light theme loaded from: {style_path}")
                return True
            except Exception as e:
                print(f"Error loading light theme from {style_path}: {e}")
    
    # Fallback to default style
    print("Warning: Could not load light theme stylesheet, using default")
    app.setStyleSheet("")
    return True

def apply_dark_theme(app):
    """Apply dark theme to the application"""
    import sys
    # Set dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # Try to load stylesheet - handle both dev and frozen (PyInstaller) modes
    possible_paths = []
    
    # Path for development mode
    resource_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
    possible_paths.append(os.path.join(resource_path, 'dark_style.qss'))
    
    # Path for PyInstaller frozen app
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(sys.executable)
        possible_paths.append(os.path.join(base_dir, 'resources', 'dark_style.qss'))
        possible_paths.append(os.path.join(base_dir, 'dark_style.qss'))
    
    # Try all possible paths
    for style_path in possible_paths:
        if os.path.exists(style_path):
            try:
                with open(style_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
                print(f"Dark theme loaded from: {style_path}")
                return True
            except Exception as e:
                print(f"Error loading dark theme from {style_path}: {e}")
    
    # Fallback - just use the palette
    print("Warning: Could not load dark theme stylesheet, using palette only")
    return True
    
    # Fallback to basic dark style
    app.setStyleSheet("""
        QWidget {
            background-color: #353535;
            color: #ffffff;
        }
        QTableWidget {
            background-color: #252525;
            color: #ffffff;
            gridline-color: #5a5a5a;
        }
        QHeaderView::section {
            background-color: #3a3a3a;
            color: #ffffff;
            padding: 5px;
            border: 1px solid #5a5a5a;
        }
        QPushButton {
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background-color: #252525;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            padding: 3px;
            border-radius: 2px;
        }
        QTabWidget::pane {
            border: 1px solid #5a5a5a;
        }
        QTabBar::tab {
            background-color: #3a3a3a;
            color: #ffffff;
            padding: 5px 10px;
            border: 1px solid #5a5a5a;
            border-bottom: none;
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
        }
        QTabBar::tab:selected {
            background-color: #4a4a4a;
        }
        QGroupBox {
            border: 1px solid #5a5a5a;
            border-radius: 3px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
    """)
    return True

def update_font_size(app=None):
    """Update the application font size"""
    if app is None:
        app = QApplication.instance()
        if app is None:
            return False
    
    font_size = get_config_value('ui', 'font_size', 10)
    font = app.font()
    font.setPointSize(font_size)
    app.setFont(font)
    return True
