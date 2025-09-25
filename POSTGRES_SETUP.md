# ePetCare PostgreSQL Setup Guide

This document explains how to set up and use PostgreSQL with your ePetCare application on Render.

## Overview

The ePetCare system now supports PostgreSQL database connectivity to the Render-hosted website. This allows for:

1. Synchronization between your local SQLite database and the remote PostgreSQL database
2. Consistent data across desktop and web applications
3. Using the deploy hook to notify the web app when data changes

## Setup Instructions

### 1. Configure PostgreSQL Connection

Run the `setup_postgres.bat` script to configure your PostgreSQL connection:

```
setup_postgres.bat
```

You'll need the following information:
- **PostgreSQL Host**: The hostname of your Render PostgreSQL database (e.g., `dpg-xxxxxxxxxxxx-a.oregon-postgres.render.com`)
- **PostgreSQL Port**: Usually `5432` (default)
- **Database Name**: The name of your database (e.g., `epetcare`)
- **Username**: Database username (e.g., `epetcare`)
- **Password**: Database password

You'll also be asked for the Render deploy hook URL:
```
https://api.render.com/deploy/srv-d3an3j95pdvs73d1co40?key=Zay8YidqwKg
```

### 2. Test the Connection

After configuring, you can test the connection by running:

```
test_postgres_connection.bat
```

This will verify:
- Connection to PostgreSQL database
- API connectivity to your Render website
- Deploy hook functionality

### 3. Manual Synchronization

To manually synchronize your local SQLite database with PostgreSQL:

```python
# From Python console or script
from vet_desktop_app.utils.postgres_sync import sync_all_tables

# Synchronize all tables
sync_all_tables()
```

## Configuration File Changes

The setup adds a new `db_sync` section to your `config.json`:

```json
{
    "db_sync": {
        "postgres": {
            "enabled": true,
            "host": "dpg-xxxxxxxxxxxx-a.oregon-postgres.render.com",
            "port": 5432,
            "database": "epetcare",
            "username": "epetcare",
            "password": "YOUR_POSTGRES_PASSWORD"
        }
    },
    "remote_database": {
        "deploy_hook": "https://api.render.com/deploy/srv-d3an3j95pdvs73d1co40?key=Zay8YidqwKg"
    }
}
```

## Render Settings

On the Render side, your application has been configured to:

1. Use PostgreSQL instead of SQLite when running on Render
2. Accept the deploy hook notification
3. Use environment variables for configuration

## Troubleshooting

If you encounter issues:

1. **Connection Problems**: Check your PostgreSQL credentials and host information
2. **Sync Failures**: Ensure your tables have compatible schemas between SQLite and PostgreSQL
3. **Deploy Hook Issues**: Verify the URL is correct and accessible from your network
4. **Missing Tables**: Run Django migrations on your Render site to create necessary tables

For additional help, check the log files:
- `postgres_test.log`: Connection test logs
- `postgres_sync.log`: Synchronization logs

## Reverting to SQLite Only

If needed, you can disable PostgreSQL synchronization by setting `"enabled": false` in the `postgres` configuration section.

## Security Note

Keep your PostgreSQL credentials and deploy hook URL confidential. Do not share your `config.json` file or commit it to public repositories.