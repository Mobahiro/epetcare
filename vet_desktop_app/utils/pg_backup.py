"""PostgreSQL backup utilities for the ePetCare desktop application.

This module provides utilities for backing up PostgreSQL data to local dump files.
"""

import os
import shutil
import subprocess
import logging
import tempfile
import datetime
from typing import Tuple, Union, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger('epetcare')

def get_backup_dir() -> str:
    """Return the backup directory path, creating it if it doesn't exist."""
    backup_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "backups"
    backup_dir.mkdir(exist_ok=True)
    return str(backup_dir)


def backup_postgres_data(pg_config: Dict[str, Any] = None) -> Tuple[bool, str]:
    """Back up PostgreSQL data using pg_dump.
    
    Args:
        pg_config: Optional dictionary with PostgreSQL connection parameters.
                  If not provided, it will be loaded from config.json.
                  
    Returns:
        Tuple of (success, result). If success is True, result contains the
        path to the backup file. If success is False, result contains an error message.
    """
    try:
        # Get PostgreSQL configuration if not provided
        if pg_config is None:
            from utils.config import load_config
            config = load_config()
            pg_config = config.get('postgres', {})
            if not pg_config:
                return False, "PostgreSQL configuration not found in config.json"
        
        # Resolve pg_dump executable path
        pg_dump_path = None

        # 1) Allow override via config
        pg_dump_override = None
        try:
            from utils.config import load_config
            cfg = load_config()
            pg_dump_override = cfg.get('postgres', {}).get('pg_dump_path')
        except Exception:
            pg_dump_override = None

        if pg_dump_override and os.path.exists(pg_dump_override):
            pg_dump_path = pg_dump_override

        # 2) If not overridden, try PATH
        if not pg_dump_path:
            pg_dump_path = shutil.which('pg_dump')

        # 3) On Windows, try common installation paths if still not found
        if not pg_dump_path and os.name == 'nt':
            common_paths = [
                r"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe",
                r"C:\\Program Files\\PostgreSQL\\15\\bin\\pg_dump.exe",
                r"C:\\Program Files\\PostgreSQL\\14\\bin\\pg_dump.exe",
                r"C:\\Program Files\\PostgreSQL\\13\\bin\\pg_dump.exe",
                r"C:\\Program Files (x86)\\PostgreSQL\\13\\bin\\pg_dump.exe",
            ]
            for p in common_paths:
                if os.path.exists(p):
                    pg_dump_path = p
                    break

        if not pg_dump_path:
            return False, (
                "pg_dump utility not found. Please install PostgreSQL client tools "
                "or set 'postgres.pg_dump_path' in config.json."
            )
        
        # Create backup filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = get_backup_dir()
        backup_filename = f"postgres_backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create a temporary .pgpass file for authentication
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as pgpass_file:
            # Format: hostname:port:database:username:password
            pgpass_content = f"{pg_config.get('host')}:{pg_config.get('port')}:{pg_config.get('database')}:{pg_config.get('user')}:{pg_config.get('password')}"
            pgpass_file.write(pgpass_content)
            pgpass_file.flush()
            pgpass_path = pgpass_file.name
            
            # Set permissions (required by pg_dump)
            os.chmod(pgpass_path, 0o600)
            
            # Set up environment
            env = os.environ.copy()
            env['PGPASSFILE'] = pgpass_path
            
            # Run pg_dump
            cmd = [
                pg_dump_path,
                '-h', pg_config.get('host'),
                '-p', str(pg_config.get('port')),
                '-U', pg_config.get('user'),
                '-d', pg_config.get('database'),
                '-w',  # Never prompt for password (use .pgpass)
                '-f', backup_path,
                '--format=p',  # Plain text format
                '--verbose'
            ]
            
            logger.debug(f"Running pg_dump: {' '.join(cmd)}")
            process = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Delete pgpass file
            os.unlink(pgpass_path)
            
            if process.returncode != 0:
                logger.error(f"pg_dump failed: {process.stderr}")
                return False, f"pg_dump failed: {process.stderr}"
            
            logger.info(f"PostgreSQL backup created at {backup_path}")
            return True, backup_path
            
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, str(e)