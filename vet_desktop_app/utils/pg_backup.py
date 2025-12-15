"""PostgreSQL backup utilities for the ePetCare desktop application.

This module provides utilities for backing up PostgreSQL data to local dump files.
"""

import os
import shutil
import subprocess
import logging
import tempfile
import datetime
from typing import Tuple, Dict, Any
from pathlib import Path
import json
from urllib.parse import urlparse

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

        # Normalize config using database_url if provided
        db_url = pg_config.get('database_url') or pg_config.get('host')
        if isinstance(db_url, str) and '://' in db_url:
            parsed = urlparse(db_url)
            # parsed.netloc may contain user:pass@host:port
            # Extract username/password
            if parsed.username:
                pg_config['user'] = parsed.username
            if parsed.password:
                pg_config['password'] = parsed.password
            # Host and port
            if parsed.hostname:
                pg_config['host'] = parsed.hostname
            if parsed.port:
                pg_config['port'] = parsed.port
            # Database name is path without leading '/'
            if parsed.path:
                pg_config['database'] = parsed.path.lstrip('/')
        
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
        pgpass_path = None
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as pgpass_file:
            # Format: hostname:port:database:username:password
            pgpass_content = f"{pg_config.get('host')}:{pg_config.get('port')}:{pg_config.get('database')}:{pg_config.get('user')}:{pg_config.get('password')}"
            pgpass_file.write(pgpass_content)
            pgpass_file.flush()
            pgpass_path = pgpass_file.name
        
        # On Windows, ensure the file handle is fully closed before use/deletion
        try:
            os.chmod(pgpass_path, 0o600)
        except Exception:
            # chmod may fail on Windows; it's safe to ignore
            pass
        
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
            '--clean',      # Add DROP statements before CREATE to avoid duplicates on restore
            '--if-exists',  # Use IF EXISTS for DROP statements to be safer
            '--no-owner',   # Do not set ownership (useful on managed DBs)
            '--no-privileges', # Do not set privileges
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
        
        # Try to delete pgpass file; if locked, log warning but do not fail backup
        try:
            os.unlink(pgpass_path)
        except Exception as del_err:
            logger.warning(f"Could not delete temporary pgpass file '{pgpass_path}': {del_err}")
        
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

def restore_postgres_data(sql_path: str, pg_config: Dict[str, Any] = None) -> Tuple[bool, str]:
    """Restore PostgreSQL data from a plain SQL dump using psql.

    Args:
        sql_path: Path to the .sql file to restore.
        pg_config: Optional dict of connection params; if None, load from config.json.

    Returns:
        (success, message). On success, message is a summary; otherwise, error details.
    """
    try:
        if not sql_path or not os.path.exists(sql_path):
            return False, f"SQL file not found: {sql_path}"

        # Load config if needed
        if pg_config is None:
            from utils.config import load_config
            config = load_config()
            pg_config = config.get('postgres', {})
            if not pg_config:
                return False, "PostgreSQL configuration not found in config.json"

        # Normalize via database_url if provided
        db_url = pg_config.get('database_url') or pg_config.get('host')
        if isinstance(db_url, str) and '://' in db_url:
            parsed = urlparse(db_url)
            if parsed.username:
                pg_config['user'] = parsed.username
            if parsed.password:
                pg_config['password'] = parsed.password
            if parsed.hostname:
                pg_config['host'] = parsed.hostname
            if parsed.port:
                pg_config['port'] = parsed.port
            if parsed.path:
                pg_config['database'] = parsed.path.lstrip('/')

        # Locate psql with multiple strategies
        psql_path = None

        # 1) Explicit override from config
        psql_override = pg_config.get('psql_path')
        if isinstance(psql_override, str) and os.path.exists(psql_override):
            psql_path = psql_override

        # 2) Infer from pg_dump_path if provided
        if not psql_path:
            dump_path = pg_config.get('pg_dump_path')
            if isinstance(dump_path, str) and os.path.exists(dump_path):
                candidate = os.path.join(os.path.dirname(dump_path), 'psql.exe' if os.name == 'nt' else 'psql')
                if os.path.exists(candidate):
                    psql_path = candidate

        # 3) Try PATH
        if not psql_path:
            psql_path = shutil.which('psql')

        # 4) On Windows, try common installation paths (include v18)
        if not psql_path and os.name == 'nt':
            common_paths = [
                r"C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe",
                r"C:\\Program Files\\PostgreSQL\\17\\bin\\psql.exe",
                r"C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe",
                r"C:\\Program Files\\PostgreSQL\\15\\bin\\psql.exe",
                r"C:\\Program Files\\PostgreSQL\\14\\bin\\psql.exe",
                r"C:\\Program Files\\PostgreSQL\\13\\bin\\psql.exe",
                r"C:\\Program Files (x86)\\PostgreSQL\\13\\bin\\psql.exe",
            ]
            for p in common_paths:
                if os.path.exists(p):
                    psql_path = p
                    break

        if not psql_path:
            return False, "psql utility not found. Please install PostgreSQL client tools or set 'postgres.psql_path' in config.json."

        # Build connection env (use sslmode if set)
        env = os.environ.copy()
        if pg_config.get('password'):
            env['PGPASSWORD'] = str(pg_config.get('password'))
        if str(pg_config.get('sslmode') or '').strip():
            env['PGSSLMODE'] = str(pg_config.get('sslmode'))

        # Optional pre-clean: drop and recreate public schema to avoid duplicate objects
        # Default is now False to prevent accidental data loss.
        pre_clean = False
        try:
            # Allow config override: postgres.pre_clean_restore
            pre_clean = bool(pg_config.get('pre_clean_restore', False))
        except Exception:
            pre_clean = False

        if pre_clean:
            clean_cmd = [
                psql_path,
                '-h', pg_config.get('host'),
                '-p', str(pg_config.get('port')),
                '-U', pg_config.get('user'),
                '-d', pg_config.get('database'),
                '-v', 'ON_ERROR_STOP=1',
                '-c', 'DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;'
            ]
            logger.debug(f"Pre-clean schema: {' '.join(clean_cmd)}")
            clean_proc = subprocess.run(clean_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if clean_proc.returncode != 0:
                logger.warning(f"Pre-clean failed, continuing: {clean_proc.stderr}")

        # Run psql restore
        cmd = [
            psql_path,
            '-h', pg_config.get('host'),
            '-p', str(pg_config.get('port')),
            '-U', pg_config.get('user'),
            '-d', pg_config.get('database'),
            '-v', 'ON_ERROR_STOP=1',
            '-f', sql_path,
        ]
        logger.debug(f"Running psql restore: {' '.join(cmd)}")
        proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            logger.error(f"psql restore failed: {proc.stderr}")
            return False, f"psql restore failed: {proc.stderr}"
        logger.info(f"Restore completed from {sql_path}")
        return True, f"Restore completed from {sql_path}"
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, str(e)