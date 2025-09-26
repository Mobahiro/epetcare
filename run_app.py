import os, sys, json, traceback 
root_dir = r'C:\epetcare' 
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
        if 'postgres' not in data: 
            needs_template = True 
    except Exception: 
        needs_template = True 
if needs_template: 
    template = { 
        'postgres': { 
            'host': '', 'port': 5432, 'database': '', 'user': '', 'password': '', 'sslmode': 'require', 'database_url': '' 
        }, 
        'app': {'auto_backup': False, 'read_only_mode': False}, 
        'ui': {'theme': 'light', 'font_size': 10} 
    } 
    with open(cfg_path, 'w') as f: json.dump(template, f, indent=4) 
    print('Created Postgres config template at config.json - please fill credentials.') 
else: 
    print('Using existing config.json') 
try: 
    print('Starting ePetCare Vet Portal...') 
    with open('main.py','r',encoding='utf-8') as f: code = compile(f.read(),'main.py','exec'); exec(code) 
except Exception as e: 
    print('\nERROR:', e) 
    traceback.print_exc() 
    input('\nPress Enter to exit...') 
