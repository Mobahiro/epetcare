# ePetCare GitHub to Render Database Guide

This guide explains how to connect your GitHub repository to Render and ensure your database stays synchronized between your local environment and the Render deployment.

## GitHub to Render Connection

Your Render deployment is now configured to connect directly to your GitHub repository. Whenever you push changes to the `main` branch, Render will automatically deploy the updated code.

## Setting Up the Database Connection

### 1. Initial Deployment

When you first deploy your application on Render, follow these steps:

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Update for Render deployment"
   git push origin main
   ```

2. Create a PostgreSQL database on Render:
   - In your Render dashboard, go to "New" → "PostgreSQL"
   - Name it `epetcare_db`
   - Choose your region and plan

3. Link the database to your web service:
   - In your web service settings, go to "Environment"
   - Add the environment variable `DATABASE_URL` with the PostgreSQL connection string from your Render database dashboard

### 2. Migrating Your Local Data

To migrate your local SQLite data to Render's PostgreSQL database:

```bash
python migrate_to_render.py
```

This script will:
- Create a data dump from your local database
- Apply migrations to the remote PostgreSQL database
- Load your data to the remote database

## Keeping Data Synchronized

### Automatic Synchronization

The updated `remote_db_client.py` automatically handles synchronization between your local desktop app and the remote database. Make sure your `config.json` has the correct settings:

```json
"remote_database": {
    "enabled": true,
    "url": "https://epetcare.onrender.com",
    "username": "YOUR_VET_USERNAME",
    "password": "YOUR_VET_PASSWORD",
    "sync_interval": 30,
    "auto_sync": true
}
```

### Manual Database Updates

If you make significant changes to your database schema:

1. Update your models in your Django application
2. Create and apply migrations locally:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Push your changes to GitHub
4. Either:
   - Wait for automatic deployment on Render, or
   - Manually deploy from the Render dashboard
5. SSH into your Render instance to apply migrations:
   ```bash
   python manage.py migrate
   ```

## Troubleshooting

### Database Connection Issues

If you encounter issues connecting to the database:

1. Check your `DATABASE_URL` environment variable in Render dashboard
2. Ensure your PostgreSQL database is up and running
3. Check if your IP is allowed in the database firewall settings
4. Run the connection test:
   ```bash
   python test_api_connection.py
   ```

### Data Synchronization Issues

If your local and remote databases get out of sync:

1. Try manual synchronization:
   ```bash
   python manage.py dumpdata > data_dump.json
   ```

2. Upload the data to your Render instance and load it:
   ```bash
   python manage.py loaddata data_dump.json
   ```

## Important Notes

1. **Production vs Development Settings**:
   - Local development uses SQLite
   - Render deployment uses PostgreSQL
   - Make sure your `settings_production.py` is properly configured

2. **Security**:
   - Never commit sensitive data like passwords or secret keys to GitHub
   - Use environment variables for sensitive information
   - Secure your API endpoints with proper authentication

3. **Automatic Deployment**:
   - Changes pushed to GitHub will trigger automatic deployment on Render
   - You can disable automatic deployments in Render dashboard if needed

## Monitoring Your Deployment

Monitor your deployment through:

1. Render dashboard - Check logs and deployment status
2. Application logs - Set up proper logging in your Django application
3. Database metrics - Monitor database performance in Render dashboard

---

For any issues or questions, refer to the documentation or contact support.