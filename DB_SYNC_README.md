# ePetCare Database Synchronization

This document explains how the database synchronization works between the ePetCare Vet Portal desktop application and the Render-hosted web application.

## Overview

ePetCare uses a dual database system:
1. **Local SQLite Database**: Used by the Vet Portal desktop application
2. **Remote PostgreSQL Database**: Used by the Render-hosted web application

These databases need to stay in sync to ensure data consistency across both platforms.

## How Synchronization Works

The synchronization process involves several components:

1. **Remote API Endpoints**: The Render website provides API endpoints for database operations:
   - `GET /api/database/sync/`: Get database info and sync status
   - `GET /api/database/download/`: Download database content
   - `POST /api/database/upload/`: Upload database changes

2. **RemoteDatabaseClient**: A Python class that handles API communications:
   - Located in `vet_desktop_app/utils/remote_db_client.py`
   - Handles authentication and API endpoint discovery
   - Manages database download/upload operations

3. **NetworkDatabaseManager**: Manages network operations for database sync:
   - Located in `vet_desktop_app/utils/network_db.py`
   - Uses RemoteDatabaseClient for API interactions
   - Provides higher-level sync functions

4. **DatabaseSyncManager**: Orchestrates the sync process:
   - Located in `vet_desktop_app/utils/db_sync.py`
   - Runs as a background thread
   - Handles sync intervals and real-time updates

## Configuration

The synchronization settings are stored in `vet_desktop_app/config.json`:

```json
{
    "database": {
        "path": "C:\\epetcare\\db.sqlite3",
        "backup_dir": "backups",
        "real_time_sync": true
    },
    "remote_database": {
        "enabled": true,
        "url": "https://epetcare.onrender.com",
        "username": "admin",
        "password": "admin",
        "sync_interval": 30,
        "auto_sync": true
    }
}
```

## Common Issues and Solutions

### 1. Connection Issues

**Symptoms**: Error messages about failed connections, timeouts, or "No connection available"

**Solutions**:
- Verify the URL in `config.json` is correct
- Check if the Render website is deployed and running
- Test network connectivity from the client machine

### 2. Authentication Problems

**Symptoms**: 401 Unauthorized or 403 Forbidden errors

**Solutions**:
- Verify username and password in `config.json`
- Make sure the user has appropriate permissions
- Check if the API token has expired

### 3. API Endpoint Discovery Failures

**Symptoms**: "No API endpoints found" or "Endpoint not found" errors

**Solutions**:
- The `fix_db_sync.py` script repairs the endpoint discovery logic
- Check if the API URLs are properly formatted in `remote_db_client.py`
- Verify that API endpoints are properly enabled in Django

### 4. Database Corruption

**Symptoms**: "database disk image is malformed" or other SQLite errors

**Solutions**:
- Restore from a backup in the `backups` directory
- Run integrity check on the database: `sqlite3 db.sqlite3 "PRAGMA integrity_check"`
- If corruption persists, you may need to recreate the database

## Diagnostic and Repair Tools

Several tools are provided to help diagnose and fix synchronization issues:

### 1. `diagnose_db_sync.py`

This script performs comprehensive diagnostics on your database sync setup:
- Checks local database integrity
- Tests connectivity to the Render API
- Verifies API endpoints and authentication
- Fixes common issues in the sync code and configuration

Usage:
```
python diagnose_db_sync.py
```

### 2. `migrate_to_render.py`

This script migrates your local database to the Render website:
- Creates a dump of your local database
- Transfers it to the Render API
- Handles initial setup and data migration

Usage:
```
python migrate_to_render.py [--force] [--check-only]
```

### 3. `monitor_db_sync.py`

This script monitors the database synchronization in real-time:
- Checks sync status at regular intervals
- Can fix common issues automatically
- Provides detailed logs of sync operations

Usage:
```
python monitor_db_sync.py [--interval SECONDS] [--fix] [--background]
```

### 4. `fix_db_sync.bat`

This batch file automates the entire fix process:
- Runs diagnostics and fixes common issues
- Migrates the database to Render
- Tests synchronization
- Restarts the Vet Portal application

Usage:
```
fix_db_sync.bat
```

## Best Practices

1. **Regular Backups**: Enable auto_backup in config.json
2. **Sync Interval**: Set an appropriate sync_interval (30-60 seconds recommended)
3. **Error Handling**: Check logs regularly for sync errors
4. **Connection Checks**: Use `diagnose_db_sync.py` to verify connections
5. **Manual Sync**: Run `migrate_to_render.py` when making major database changes