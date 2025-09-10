#!/bin/bash

# Run the ePetCare Vet Desktop application

# Change to the script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install or update dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Deactivate virtual environment
deactivate
