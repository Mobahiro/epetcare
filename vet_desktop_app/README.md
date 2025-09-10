# ePetCare Vet Desktop Application

A standalone desktop application for veterinarians to access the ePetCare system. This application connects to the same database as the ePetCare web application, allowing veterinarians to manage appointments, patients, and medical records from their desktop.

## Features

- **Patient Management**: View and manage pet and owner information
- **Appointment Scheduling**: Schedule, view, and manage appointments
- **Medical Records**: Access and update medical records, prescriptions, and treatments
- **Offline Mode**: Work offline and sync changes when back online
- **Database Integration**: Connects to the same SQLite database as the ePetCare web application

## Installation

### Prerequisites

- Python 3.8 or higher (compatible with Python 3.13)
- PySide6
- Access to the ePetCare database

### Install from Source

1. Clone the repository or download the source code
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python main.py
```

### Install from Binary

1. Download the latest installer from the releases page
2. Run the installer and follow the instructions
3. Launch the application from the desktop shortcut or start menu

## Configuration

The application can be configured through the Settings menu. Key settings include:

- **Database Path**: Path to the SQLite database file
- **Backup Directory**: Directory to store database backups
- **Offline Mode**: Enable/disable offline mode
- **Sync Interval**: How often to sync changes when in offline mode
- **UI Theme**: Light or dark theme

## Building the Installer

To build the installer, you need PyInstaller:

```bash
pip install pyinstaller
```

Then run:

```bash
pyinstaller epetcare_vet_desktop.spec
```

This will create a `dist` directory containing the bundled application.

## License

This software is proprietary and confidential. Unauthorized copying, transferring, or reproduction of the contents of this software, via any medium, is strictly prohibited.

## Support

For support, please contact the ePetCare support team at support@epetcare.local.
