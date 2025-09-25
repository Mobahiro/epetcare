"""
ePetCare Database Sync Dashboard

This script provides a simple web-based dashboard to monitor the status
of the database synchronization between the local Vet Portal and the
remote Render website.

Usage: python sync_dashboard.py
"""

import os
import sys
import json
import time
import logging
import sqlite3
import threading
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync_dashboard.log')
    ]
)
logger = logging.getLogger('epetcare_dashboard')

# Global variables
config = None
sync_status = {
    "last_check": None,
    "last_success": None,
    "last_failure": None,
    "errors": [],
    "status": "unknown",
    "local_db": {
        "path": None,
        "size": None,
        "last_modified": None,
        "tables": 0,
        "records": {}
    },
    "remote_api": {
        "url": None,
        "status": "unknown",
        "endpoints": [],
        "last_check": None
    }
}
monitor_thread = None
shutdown_event = threading.Event()

def load_config():
    """Load the configuration from config.json"""
    try:
        config_path = os.path.join('vet_desktop_app', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def update_local_db_status():
    """Update the local database status"""
    global sync_status, config
    
    if not config:
        return
    
    db_path = config.get('database', {}).get('path')
    if not db_path or not os.path.exists(db_path):
        sync_status["local_db"]["status"] = "not_found"
        return
    
    # Update basic file info
    sync_status["local_db"]["path"] = db_path
    sync_status["local_db"]["size"] = os.path.getsize(db_path) / (1024 * 1024)  # Size in MB
    sync_status["local_db"]["last_modified"] = datetime.fromtimestamp(
        os.path.getmtime(db_path)
    ).strftime("%Y-%m-%d %H:%M:%S")
    
    # Check database integrity and content
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        sync_status["local_db"]["integrity"] = integrity
        
        # Count tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        sync_status["local_db"]["tables"] = len(tables)
        
        # Count records in key tables
        key_tables = [
            'auth_user', 'clinic_owner', 'clinic_pet', 'clinic_appointment', 
            'clinic_medicalrecord', 'clinic_prescription'
        ]
        
        record_counts = {}
        for table in key_tables:
            if table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    record_counts[table] = count
                except:
                    record_counts[table] = "error"
            else:
                record_counts[table] = "missing"
        
        sync_status["local_db"]["records"] = record_counts
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        sync_status["local_db"]["integrity"] = "error"

def update_remote_api_status():
    """Update the remote API status"""
    global sync_status, config
    
    if not config:
        return
    
    remote_db = config.get('remote_database', {})
    url = remote_db.get('url')
    username = remote_db.get('username')
    password = remote_db.get('password')
    
    if not url:
        sync_status["remote_api"]["status"] = "not_configured"
        return
    
    sync_status["remote_api"]["url"] = url
    sync_status["remote_api"]["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Test API connection
    try:
        import requests
        
        # Test base URL
        response = requests.get(url, timeout=10)
        sync_status["remote_api"]["status"] = "online" if response.status_code < 400 else "error"
        
        # Test auth endpoints
        if username and password:
            auth_endpoints = [
                f"{url}/api-token-auth/",
                f"{url}/api/token/",
                f"{url}/vet_portal/api-token-auth/",
            ]
            
            for auth_url in auth_endpoints:
                try:
                    auth_response = requests.post(
                        auth_url,
                        data={"username": username, "password": password},
                        timeout=10
                    )
                    
                    if auth_response.status_code == 200:
                        sync_status["remote_api"]["auth_endpoint"] = auth_url
                        sync_status["remote_api"]["endpoints"].append(auth_url)
                        break
                except:
                    pass
        
        # Test API endpoints
        api_paths = [
            '/api',
            '/vet_portal/api',
            '/api/v1'
        ]
        
        working_endpoints = []
        
        for api_path in api_paths:
            # Test database sync endpoints
            sync_url = f"{url}{api_path}/database/sync/"
            try:
                response = requests.get(sync_url, timeout=10)
                if response.status_code == 200:
                    working_endpoints.append(sync_url)
            except:
                pass
            
            # Test database download endpoints
            download_url = f"{url}{api_path}/database/download/"
            try:
                response = requests.head(download_url, timeout=10)
                if response.status_code == 200:
                    working_endpoints.append(download_url)
            except:
                pass
        
        sync_status["remote_api"]["endpoints"] = working_endpoints
        
    except Exception as e:
        logger.error(f"Error checking remote API: {e}")
        sync_status["remote_api"]["status"] = "error"
        sync_status["remote_api"]["error"] = str(e)

def check_sync_status():
    """Check the database synchronization status"""
    global sync_status, config
    
    sync_status["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update local database status
    update_local_db_status()
    
    # Update remote API status
    update_remote_api_status()
    
    # Check sync logs
    try:
        log_path = "db_sync_monitor.log"
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_lines = f.readlines()[-100:]  # Last 100 lines
                
                # Look for success/error messages
                for line in reversed(log_lines):
                    if "Database sync successful" in line:
                        sync_status["last_success"] = line.split(" - ")[0]
                        sync_status["status"] = "success"
                        break
                    elif "Database sync failed" in line or "Error" in line:
                        sync_status["last_failure"] = line.split(" - ")[0]
                        sync_status["status"] = "error"
                        
                        # Extract error message
                        error_msg = line.split(" - ")[-1].strip()
                        if error_msg not in sync_status["errors"]:
                            sync_status["errors"].append(error_msg)
                        break
    except Exception as e:
        logger.error(f"Error checking sync logs: {e}")
    
    # Check for running sync monitor
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'python' in cmdline[0].lower() and any('monitor_db_sync.py' in cmd for cmd in cmdline):
                sync_status["monitor_running"] = True
                break
        else:
            sync_status["monitor_running"] = False
    except:
        # psutil might not be available
        sync_status["monitor_running"] = "unknown"

def monitor_thread_func(interval=30):
    """Background thread for monitoring database sync"""
    global sync_status
    
    logger.info(f"Monitor thread started with interval {interval} seconds")
    
    while not shutdown_event.is_set():
        try:
            logger.info("Checking database sync status...")
            check_sync_status()
        except Exception as e:
            logger.error(f"Error in monitor thread: {e}")
        
        # Wait for the next interval or until shutdown
        shutdown_event.wait(interval)
    
    logger.info("Monitor thread stopped")

class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/':
            self.send_dashboard()
        elif path == '/status':
            self.send_status_json()
        elif path == '/check':
            check_sync_status()
            self.send_redirect('/')
        elif path == '/sync':
            self.trigger_sync()
            self.send_redirect('/')
        elif path == '/fix':
            self.trigger_fix()
            self.send_redirect('/')
        elif path == '/restart-monitor':
            self.restart_monitor()
            self.send_redirect('/')
        else:
            self.send_error(404, "Not Found")
    
    def send_dashboard(self):
        """Send the dashboard HTML"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ePetCare Database Sync Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        h1 {{
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .status-panel {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .status-box {{
            flex: 1;
            margin: 0 10px;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }}
        .success {{
            background-color: #d4edda;
            border-left: 5px solid #28a745;
        }}
        .error {{
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
        }}
        .warning {{
            background-color: #fff3cd;
            border-left: 5px solid #ffc107;
        }}
        .info {{
            background-color: #d1ecf1;
            border-left: 5px solid #17a2b8;
        }}
        .unknown {{
            background-color: #e2e3e5;
            border-left: 5px solid #6c757d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        table, th, td {{
            border: 1px solid #ddd;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .btn-group {{
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }}
        .btn {{
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}
        .btn-primary {{
            background-color: #007bff;
            color: white;
        }}
        .btn-success {{
            background-color: #28a745;
            color: white;
        }}
        .btn-warning {{
            background-color: #ffc107;
            color: #212529;
        }}
        .btn-danger {{
            background-color: #dc3545;
            color: white;
        }}
        .timestamp {{
            font-size: 0.8em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ePetCare Database Sync Dashboard</h1>
        
        <div class="status-panel">
            <div class="status-box" id="overall-status">
                <h3>Overall Status</h3>
                <div id="status-indicator">Loading...</div>
            </div>
            
            <div class="status-box" id="local-db-status">
                <h3>Local Database</h3>
                <div id="local-db-info">Loading...</div>
            </div>
            
            <div class="status-box" id="remote-api-status">
                <h3>Remote API</h3>
                <div id="remote-api-info">Loading...</div>
            </div>
        </div>
        
        <h2>Sync Details</h2>
        <table>
            <tr>
                <th>Last Check</th>
                <td id="last-check">Loading...</td>
            </tr>
            <tr>
                <th>Last Successful Sync</th>
                <td id="last-success">Loading...</td>
            </tr>
            <tr>
                <th>Last Failed Sync</th>
                <td id="last-failure">Loading...</td>
            </tr>
            <tr>
                <th>Monitor Service</th>
                <td id="monitor-status">Loading...</td>
            </tr>
        </table>
        
        <h2>Database Details</h2>
        <table>
            <tr>
                <th>Table</th>
                <th>Records</th>
            </tr>
            <tbody id="table-records">
                <tr><td colspan="2">Loading...</td></tr>
            </tbody>
        </table>
        
        <h2>Error Log</h2>
        <div id="error-log">Loading...</div>
        
        <div class="btn-group">
            <a href="/check" class="btn btn-primary">Check Now</a>
            <a href="/sync" class="btn btn-success">Trigger Sync</a>
            <a href="/fix" class="btn btn-warning">Fix Issues</a>
            <a href="/restart-monitor" class="btn btn-danger">Restart Monitor</a>
        </div>
        
        <p class="timestamp">Dashboard updated: <span id="update-time"></span></p>
    </div>
    
    <script>
        // Auto-refresh status every 5 seconds
        setInterval(fetchStatus, 5000);
        
        // Initial fetch
        fetchStatus();
        
        function fetchStatus() {{
            fetch('/status')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error fetching status:', error));
        }}
        
        function updateDashboard(data) {{
            // Update overall status
            const overallStatus = document.getElementById('status-indicator');
            let statusClass = 'unknown';
            let statusText = 'Unknown';
            
            switch (data.status) {{
                case 'success':
                    statusClass = 'success';
                    statusText = 'Synchronized';
                    break;
                case 'error':
                    statusClass = 'error';
                    statusText = 'Error';
                    break;
                case 'disabled':
                    statusClass = 'warning';
                    statusText = 'Disabled';
                    break;
                case 'unknown':
                    statusClass = 'unknown';
                    statusText = 'Unknown';
                    break;
            }}
            
            overallStatus.className = statusClass;
            overallStatus.innerHTML = `<strong>${statusText}</strong>`;
            
            // Update local database info
            const localDbInfo = document.getElementById('local-db-info');
            const dbPath = data.local_db.path || 'Not configured';
            const dbSize = data.local_db.size ? `${data.local_db.size.toFixed(2)} MB` : 'Unknown';
            const dbModified = data.local_db.last_modified || 'Unknown';
            const dbTables = data.local_db.tables || 'Unknown';
            const dbIntegrity = data.local_db.integrity || 'Unknown';
            
            localDbInfo.innerHTML = `
                <p><strong>Path:</strong> ${dbPath}</p>
                <p><strong>Size:</strong> ${dbSize}</p>
                <p><strong>Modified:</strong> ${dbModified}</p>
                <p><strong>Tables:</strong> ${dbTables}</p>
                <p><strong>Integrity:</strong> ${dbIntegrity}</p>
            `;
            
            // Update remote API info
            const remoteApiInfo = document.getElementById('remote-api-info');
            const apiUrl = data.remote_api.url || 'Not configured';
            const apiStatus = data.remote_api.status || 'Unknown';
            const apiEndpoints = (data.remote_api.endpoints || []).length;
            const apiLastCheck = data.remote_api.last_check || 'Never';
            
            let apiStatusText = apiStatus;
            if (apiStatus === 'online') {{
                apiStatusText = '<span style="color: green;">Online</span>';
            }} else if (apiStatus === 'error') {{
                apiStatusText = '<span style="color: red;">Error</span>';
            }}
            
            remoteApiInfo.innerHTML = `
                <p><strong>URL:</strong> ${apiUrl}</p>
                <p><strong>Status:</strong> ${apiStatusText}</p>
                <p><strong>Working Endpoints:</strong> ${apiEndpoints}</p>
                <p><strong>Last Check:</strong> ${apiLastCheck}</p>
            `;
            
            // Update sync details
            document.getElementById('last-check').textContent = data.last_check || 'Never';
            document.getElementById('last-success').textContent = data.last_success || 'Never';
            document.getElementById('last-failure').textContent = data.last_failure || 'Never';
            
            // Update monitor status
            const monitorStatus = document.getElementById('monitor-status');
            if (data.monitor_running === true) {{
                monitorStatus.innerHTML = '<span style="color: green;">Running</span>';
            }} else if (data.monitor_running === false) {{
                monitorStatus.innerHTML = '<span style="color: red;">Stopped</span>';
            }} else {{
                monitorStatus.textContent = 'Unknown';
            }}
            
            // Update table records
            const tableRecords = document.getElementById('table-records');
            let tableHtml = '';
            
            const records = data.local_db.records || {{}};
            for (const table in records) {{
                const count = records[table];
                let countText = count;
                
                if (count === 'missing') {{
                    countText = '<span style="color: red;">Table missing</span>';
                }} else if (count === 'error') {{
                    countText = '<span style="color: red;">Error</span>';
                }}
                
                tableHtml += `
                    <tr>
                        <td>${table}</td>
                        <td>${countText}</td>
                    </tr>
                `;
            }}
            
            if (tableHtml) {{
                tableRecords.innerHTML = tableHtml;
            }} else {{
                tableRecords.innerHTML = '<tr><td colspan="2">No data available</td></tr>';
            }}
            
            // Update error log
            const errorLog = document.getElementById('error-log');
            const errors = data.errors || [];
            
            if (errors.length > 0) {{
                let errorHtml = '<ul>';
                for (const error of errors) {{
                    errorHtml += `<li>${error}</li>`;
                }}
                errorHtml += '</ul>';
                errorLog.innerHTML = errorHtml;
            }} else {{
                errorLog.innerHTML = '<p>No errors reported</p>';
            }}
            
            // Update timestamp
            document.getElementById('update-time').textContent = new Date().toLocaleString();
        }}
    </script>
</body>
</html>
"""
        self.wfile.write(html.encode('utf-8'))
    
    def send_status_json(self):
        """Send the current status as JSON"""
        global sync_status
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        self.wfile.write(json.dumps(sync_status).encode('utf-8'))
    
    def send_redirect(self, location):
        """Send a redirect response"""
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()
    
    def trigger_sync(self):
        """Trigger a manual database sync"""
        try:
            # Run the monitor_db_sync.py script
            import subprocess
            subprocess.Popen([sys.executable, 'monitor_db_sync.py'])
            logger.info("Manual sync triggered")
        except Exception as e:
            logger.error(f"Error triggering sync: {e}")
    
    def trigger_fix(self):
        """Trigger database fix"""
        try:
            # Run the diagnose_db_sync.py script
            import subprocess
            subprocess.Popen([sys.executable, 'diagnose_db_sync.py'])
            logger.info("Database fix triggered")
        except Exception as e:
            logger.error(f"Error triggering fix: {e}")
    
    def restart_monitor(self):
        """Restart the monitor service"""
        try:
            # Kill existing monitor processes
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'python' in cmdline[0].lower() and any('monitor_db_sync.py' in cmd for cmd in cmdline):
                        proc.terminate()
                except:
                    pass
            
            # Start new monitor process
            import subprocess
            subprocess.Popen([sys.executable, 'monitor_db_sync.py', '--background'])
            logger.info("Monitor service restarted")
        except Exception as e:
            logger.error(f"Error restarting monitor: {e}")
    
    def log_message(self, format, *args):
        """Override to redirect HTTP server logs to our logger"""
        logger.info("%s - %s" % (self.address_string(), format % args))

def main():
    global config, monitor_thread
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='ePetCare Database Sync Dashboard')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the dashboard on')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    args = parser.parse_args()
    
    print(f"Starting ePetCare Database Sync Dashboard on http://localhost:{args.port}")
    
    # Load configuration
    config = load_config()
    
    # Initial status check
    check_sync_status()
    
    # Start monitor thread
    monitor_thread = threading.Thread(
        target=monitor_thread_func,
        daemon=True
    )
    monitor_thread.start()
    
    # Start HTTP server
    server = HTTPServer(('localhost', args.port), DashboardHandler)
    
    # Open browser
    if not args.no_browser:
        url = f"http://localhost:{args.port}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        shutdown_event.set()
        server.server_close()
        print("Server stopped")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Error: {e}")