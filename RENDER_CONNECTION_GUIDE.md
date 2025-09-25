# ePetCare Render Connection Troubleshooting Guide

This guide will help you fix issues connecting your ePetCare Vet Desktop application to the Render-hosted backend.

## Common Issues and Solutions

### 1. Authentication Errors (404 Not Found)

This happens when the desktop application is using an incorrect API URL format. The desktop app may be trying to access `/vet_portal/api` endpoints, but the API routes are set up differently on Render.

**Solution:**
1. Run `python update_config.py` to fix the URL format in your config.json file
2. The script will change the URL from `https://epetcare.onrender.com/vet_portal/api` to `https://epetcare.onrender.com/api`

### 2. Database Corruption ("database disk image is malformed")

This happens when the SQLite database file gets corrupted, possibly due to synchronization issues.

**Solution:**
1. Run `python fix_render_connection.py` to repair the database
2. The script will create a backup of your database and attempt to recover it
3. If recovery is not possible, it will create a new empty database

### 3. Testing the Connection

To verify your connection to the Render-hosted backend:

```
python test_api_connection.py
```

This script will test various API endpoints and provide recommendations on which URL format to use.

## Quick Start Guide

If you're having issues with the ePetCare Vet Desktop application connecting to Render, follow these steps:

1. **Fix Database Corruption**
   ```
   python fix_render_connection.py
   ```

2. **Update API URL Configuration**
   ```
   python update_config.py
   ```

3. **Test the Connection**
   ```
   python test_api_connection.py
   ```

4. **Launch the Application**
   ```
   vetportal_fixed.bat
   ```

## Advanced Troubleshooting

### Checking Render Deployment Status

1. Log in to your Render dashboard
2. Check if the ePetCare service is showing as "Live"
3. Check for any error messages in the logs

### API URL Format

For Render deployments, the correct API URL format should be:
- `https://epetcare.onrender.com/api` (not `/vet_portal/api`)

### Database Synchronization

The desktop application syncs with the remote database using these endpoints:
- GET `/api/database/sync/` - Gets database info
- GET `/api/database/download/` - Downloads database
- POST `/api/database/upload/` - Uploads local changes

### Configuration File

The configuration file is located at `vet_desktop_app/config.json`. Key settings:

- `remote_database.url` - The base URL of the API
- `remote_database.username` - Your vet username
- `remote_database.password` - Your vet password
- `remote_database.auto_sync` - Whether to sync automatically

## Manual Fixes

### Manually Update API URL

1. Open `vet_desktop_app/config.json` in a text editor
2. Find the `remote_database` section
3. Change the `url` value to `https://epetcare.onrender.com/api`
4. Save the file

### Manually Create a New Database

If the database is completely corrupted:

1. Delete `db.sqlite3` and `vet_desktop_app/data/db.sqlite3`
2. Run `python manage.py migrate` to create a new empty database
3. Run `python create_test_user.py` to create a test user

### Update Remote Client Code

To use the improved client code:

1. Copy `vet_desktop_app/utils/remote_db_client_fixed.py` to `vet_desktop_app/utils/remote_db_client.py`

## Support

If you continue to experience issues, please:
1. Check the logs in `logs/app.log`
2. Run `python test_api_connection.py` and review the results
3. Contact support with the error details and log files