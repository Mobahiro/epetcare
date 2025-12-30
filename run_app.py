import os, sys, json, traceback 
root_dir = r'C:\Users\hamme\Documents\Projects\epetcare' 
app_dir = os.path.join(root_dir, 'vet_desktop_app') 
sys.path.insert(0, root_dir) 
sys.path.insert(0, app_dir) 
os.chdir(app_dir) 
cfg_path = os.path.join(app_dir, 'config.json') 
needs_template = False 
if not os.path.exists(cfg_path): 
    needs_template = True 
else: 
    try: 
        data = json.load(open(cfg_path, 'r')) 
        if 'postgres' not in data or 'app' not in data or 'server_url' not in data.get('app', {}): 
            needs_template = True 
    except Exception: 
        needs_template = True 
if needs_template: 
    template = { 
        'postgres': { 
            'host': 'YOUR_DB_HOST', 
            'port': 5432, 
            'database': 'YOUR_DB_NAME', 
            'user': 'YOUR_DB_USER', 
            'password': 'YOUR_DB_PASSWORD', 
            'sslmode': 'require', 
            'database_url': '', 
            'pg_dump_path': '' 
        }, 
        'app': { 
            'offline_mode': False, 
            'sync_interval': 300, 
            'auto_backup': True, 
            'server_url': 'https://epetcare.onrender.com' 
        }, 
        'ui': {'theme': 'light', 'font_size': 10} 
    } 
    with open(cfg_path, 'w') as f: json.dump(template, f, indent=4) 
    print('Created config.json with server_url and postgres template - please fill credentials if needed.') 
else: 
    try: 
        data = json.load(open(cfg_path, 'r')) 
        print(f'Using existing config.json (server_url: {srv})') 
    except Exception: 
        print('Using existing config.json') 
try: 
    print('Starting ePetCare Vet Portal...') 
    with open('main.py','r',encoding='utf-8') as f: code = compile(f.read(),'main.py','exec'); exec(code) 
except Exception as e: 
    print('\nERROR:', e) 
    traceback.print_exc() 
    input('\nPress Enter to exit...') 
