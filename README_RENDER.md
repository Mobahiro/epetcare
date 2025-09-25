# ePetCare Render Deployment

This folder contains the necessary files to deploy your ePetCare application on Render and connect your vet portal desktop application to the cloud database.

## Setup Instructions

### 1. Deploy to Render

First, follow the instructions in the `RENDER_DEPLOYMENT.md` file to deploy your application to Render. This includes:

- Setting up a PostgreSQL database on Render
- Deploying the Django application
- Migrating your data

### 2. Connect Your Local Vet Portal to Render

After you've successfully deployed the application and set up the PostgreSQL database, you can connect your local vet portal application to it:

1. Run the setup script:
```
setup_render_connection.bat
```

2. Enter your Render application URL when prompted:
```
https://your-app-name.onrender.com
```

3. Enter the vet username and password when prompted.

4. The script will test the connection and start the vet portal application.

### 3. Manage Database Synchronization

You can use the `db_sync_helper.py` script to manage the synchronization between your local vet portal and the remote database:

```
python db_sync_helper.py status   # Check connection status
python db_sync_helper.py sync     # Force synchronization
python db_sync_helper.py upload   # Upload local changes
python db_sync_helper.py download # Download the remote database
python db_sync_helper.py configure # Update configuration settings
```

## File Structure

- `RENDER_DEPLOYMENT.md`: Detailed instructions for deploying to Render
- `setup_render_connection.bat`: Script to set up the connection to Render
- `test_render_connection.py`: Script to test the connection to Render
- `db_sync_helper.py`: Script to manage database synchronization
- `vet_desktop_app/`: Folder containing the vet portal desktop application
  - `utils/remote_db_client.py`: Module for connecting to the remote database
  - `utils/db_sync.py`: Module for synchronizing the database

## Troubleshooting

If you encounter issues connecting to the Render database:

1. Verify that your Render application is running properly
2. Check that the PostgreSQL database is accessible
3. Ensure the correct URL, username, and password are configured
4. Run `python test_render_connection.py` to test the connection
5. Check the logs in the `vet_desktop_app/logs` directory

## Support

For additional help, refer to the Render documentation or contact the application support team.