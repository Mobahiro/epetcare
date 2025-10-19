"""
Configuration utilities for the ePetCare Vet Desktop application.
"""

import os
import json
from pathlib import Path


CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')

# New unified default config oriented around PostgreSQL (remote canonical database)
# We intentionally keep the old 'database' section for backward compatibility until
# the settings UI is fully migrated; 'database.path' is no longer used for data access.
DEFAULT_CONFIG = {
    'postgres': {
        'host': 'YOUR_DB_HOST',         # e.g. dpg-xxxxx.render.com
        'port': 5432,
        'database': 'YOUR_DB_NAME',     # e.g. epetcare
        'user': 'YOUR_DB_USER',
        'password': 'YOUR_DB_PASSWORD',
        'sslmode': 'require',
        'database_url': '',              # Optional full URL overrides discrete fields
        'pg_dump_path': ''               # Optional absolute path to pg_dump executable (Windows)
    },
    'database': {  # legacy / soon to be removed from UI
        'path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'db.sqlite3'),
        'backup_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups'),
    },
    'app': {
        'offline_mode': False,
        'sync_interval': 300,  # seconds (legacy sync no longer active; may repurpose later)
        'auto_backup': True,   # applies only to legacy local sqlite backups
        'server_url': 'https://epetcare.onrender.com',  # Production server URL
        'fallback_server_urls': ['http://localhost:8000'],  # Try local dev server as fallback
    },
    'ui': {
        'theme': 'light',
        'font_size': 10,
    }
}


def load_config():
    """Load configuration from file or create default if not exists"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)

            # Migration: ensure postgres section exists; if migrating from old schema
            # that had remote_database/database only, inject postgres placeholders.
            if 'postgres' not in config:
                config['postgres'] = DEFAULT_CONFIG['postgres'].copy()

                # Attempt to derive values from any legacy environment variables (optional)
                # or from a DATABASE_URL if the user manually added one elsewhere.
                env_url = os.environ.get('DATABASE_URL')
                if env_url and not config['postgres'].get('database_url'):
                    config['postgres']['database_url'] = env_url

            # Shallow merge each section to retain new keys while preserving user values.
            merged_config = {}
            for section, default_values in DEFAULT_CONFIG.items():
                existing_values = config.get(section, {})
                if isinstance(default_values, dict):
                    merged = default_values.copy()
                    merged.update(existing_values)
                    merged_config[section] = merged
                else:
                    merged_config[section] = existing_values if section in config else default_values

            # Include any extra user-defined sections not in defaults
            for section, values in config.items():
                if section not in merged_config:
                    merged_config[section] = values

            # If we performed a migration (added postgres), persist it back to disk once.
            if merged_config != config:
                save_config(merged_config)

            return merged_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config):
    """Save configuration to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except IOError as e:
        print(f"Error saving config: {e}")
        return False


def get_config_value(section, key, default=None):
    """Get a specific configuration value"""
    config = load_config()
    return config.get(section, {}).get(key, default)


def set_config_value(section, key, value):
    """Set a specific configuration value"""
    config = load_config()
    if section not in config:
        config[section] = {}
    config[section][key] = value
    return save_config(config)

# Backward compatibility shim
def get_config():
    """Return the full configuration dict (legacy compatibility).

    Older modules import `get_config` expecting a dictionary with .get().
    This wraps load_config() to satisfy that contract.
    """
    return load_config()
