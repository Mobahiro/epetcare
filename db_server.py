"""
Database API server for ePetCare.
This script starts a simple Flask server that provides API access to the SQLite database.
"""

import os
import sys
import json
import sqlite3
import logging
import argparse
from datetime import datetime
from flask import Flask, request, jsonify, send_file, g

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('epetcare_db_server')

# Create Flask app
app = Flask(__name__)

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
API_TOKEN = None  # Set this to a secure token for production use
PORT = 5000
HOST = '0.0.0.0'  # Listen on all interfaces

# Database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Authentication decorator
def require_auth(f):
    def decorated(*args, **kwargs):
        if API_TOKEN:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Unauthorized'}), 401
            
            token = auth_header.split(' ')[1]
            if token != API_TOKEN:
                return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    decorated.__name__ = f.__name__
    return decorated

# API routes
@app.route('/api/status', methods=['GET'])
def status():
    """Check server status"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'database': os.path.basename(DATABASE_PATH)
    })

@app.route('/api/download', methods=['GET'])
@require_auth
def download_database():
    """Download the database file"""
    if not os.path.exists(DATABASE_PATH):
        return jsonify({'error': 'Database file not found'}), 404
    
    # Create a backup connection to ensure all changes are flushed
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute('PRAGMA wal_checkpoint(FULL)')
    conn.close()
    
    return send_file(DATABASE_PATH, as_attachment=True)

@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_database():
    """Upload a database file"""
    if 'database' not in request.files:
        return jsonify({'error': 'No database file provided'}), 400
    
    file = request.files['database']
    
    # Save to a temporary file first
    temp_path = f"{DATABASE_PATH}.temp"
    file.save(temp_path)
    
    try:
        # Verify the uploaded file is a valid SQLite database
        conn = sqlite3.connect(temp_path)
        conn.execute('PRAGMA integrity_check')
        conn.close()
        
        # Create a backup of the current database
        backup_path = f"{DATABASE_PATH}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if os.path.exists(DATABASE_PATH):
            os.rename(DATABASE_PATH, backup_path)
        
        # Move the temporary file to the database path
        os.rename(temp_path, DATABASE_PATH)
        
        return jsonify({'success': True, 'message': 'Database uploaded successfully'})
        
    except sqlite3.Error as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': f'Invalid SQLite database: {str(e)}'}), 400
    
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500

@app.route('/api/tables', methods=['GET'])
@require_auth
def list_tables():
    """List all tables in the database"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
@require_auth
def execute_query():
    """Execute a SQL query"""
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400
    
    query = data['query']
    params = data.get('params', [])
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(query, params)
        
        if query.strip().upper().startswith(('SELECT')):
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return jsonify({'results': results})
        else:
            db.commit()
            return jsonify({'success': True, 'affected_rows': cursor.rowcount})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Main entry point
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ePetCare Database API Server')
    parser.add_argument('--host', default=HOST, help=f'Host to listen on (default: {HOST})')
    parser.add_argument('--port', type=int, default=PORT, help=f'Port to listen on (default: {PORT})')
    parser.add_argument('--database', default=DATABASE_PATH, help=f'Path to the database file (default: {DATABASE_PATH})')
    parser.add_argument('--token', default=API_TOKEN, help='API token for authentication (default: none)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Update configuration
    DATABASE_PATH = args.database
    API_TOKEN = args.token
    PORT = args.port
    HOST = args.host
    
    # Log configuration
    logger.info(f"Starting ePetCare Database API Server")
    logger.info(f"Database path: {DATABASE_PATH}")
    logger.info(f"Listening on: {HOST}:{PORT}")
    logger.info(f"Authentication: {'Enabled' if API_TOKEN else 'Disabled'}")
    
    # Start the server
    app.run(host=HOST, port=PORT, debug=args.debug)
