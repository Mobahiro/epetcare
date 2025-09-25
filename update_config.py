# Update config.json to fix the Render URL configuration and ensure proper API path

import json
import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='config_update.log',
    filemode='w'
)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Path to config.json
config_file = os.path.join('vet_desktop_app', 'config.json')

try:
    # Load the current configuration
    print(f"Reading configuration from {config_file}...")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Get the current remote database URL
    current_url = config.get('remote_database', {}).get('url', '')
    print(f"Current remote database URL: {current_url}")
    
    # Check and fix the URL
    if current_url.endswith('/vet_portal/api'):
        # URL is incorrectly formatted, needs fixing
        base_url = current_url.replace('/vet_portal/api', '')
        new_url = f"{base_url}/api"
        
        print(f"Updating URL from: {current_url}")
        print(f"                to: {new_url}")
        
        # Update the configuration
        config['remote_database']['url'] = new_url
        
        # Save the updated configuration
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        print("Configuration updated successfully.")
        print("\nReminder: After updating the configuration, you should:")
        print("1. Start the application using vetportal_fixed.bat")
        print("2. If you encounter any issues, run fix_render_connection.py")
    else:
        print("The URL format appears to be correct. No changes needed.")
        
    print("\nDone!")
    
except Exception as e:
    print(f"Error: {e}")
    logging.exception(f"Exception occurred: {e}")