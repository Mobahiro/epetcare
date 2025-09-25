import os, sys, traceback 
# Set up paths 
root_dir = r'C:\epetcare' 
app_dir = os.path.join(root_dir, 'vet_desktop_app') 
sys.path.insert(0, root_dir) 
sys.path.insert(0, app_dir) 
# Change to the app directory 
os.chdir(app_dir) 
# Create config.json 
config = { 
    "database": { 
        "path": os.path.join(root_dir, "db.sqlite3").replace("\\", "\\\\"), 
        "backup_dir": "backups", 
        "real_time_sync": True 
    }, 
    "remote_database": { 
        "enabled": True, 
        "url": "https://epetcare.onrender.com", 
        "username": "YOUR_VET_USERNAME", 
        "password": "YOUR_VET_PASSWORD", 
        "sync_interval": 30, 
        "auto_sync": True 
    }, 
    "app": { 
        "offline_mode": False, 
        "sync_interval": 5, 
        "auto_backup": True 
    }, 
    "ui": { 
        "theme": "light", 
        "font_size": 10 
    } 
} 
import json 
with open('config.json', 'w') as f: 
    json.dump(config, f, indent=4) 
# Create __init__.py files if they don't exist 
for dir_path in ['', 'models', 'views', 'utils']: 
    init_file = os.path.join(dir_path, '__init__.py') 
    if not os.path.exists(init_file): 
        with open(init_file, 'w') as f: 
            f.write('# Auto-generated __init__.py file') 
# Create data directory if it doesn't exist 
os.makedirs(os.path.join(app_dir, 'data'), exist_ok=True) 
# Run the application 
try: 
    print("Starting ePetCare Vet Portal...") 
    print("Please wait for the application window to appear...") 
    with open('main.py') as f: 
        code = compile(f.read(), 'main.py', 'exec') 
        exec(code) 
except Exception as e: 
    print(f"\nERROR: {e}") 
    traceback.print_exc() 
    input("\nPress Enter to exit...") 
