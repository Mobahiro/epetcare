"""
Configuration utilities for the ePetCare Vet Desktop application.
"""

import os
import json
from pathlib import Path


CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
DEFAULT_CONFIG = {
    'database': {
        'path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'db.sqlite3'),
        'backup_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups'),
    },
    'app': {
        'offline_mode': False,
        'sync_interval': 300,  # 5 minutes
        'auto_backup': True,
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
                # Merge with defaults to ensure all keys exist
                merged_config = DEFAULT_CONFIG.copy()
                for section, values in config.items():
                    if section in merged_config:
                        merged_config[section].update(values)
                    else:
                        merged_config[section] = values
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
