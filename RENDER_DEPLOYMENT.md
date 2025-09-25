# Deploying ePetCare on Render

This document provides step-by-step instructions for deploying the ePetCare application on Render, ensuring that both the main website and vet portal can access the same database in real-time.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Preparing Your Application](#preparing-your-application)
3. [Deploying to Render](#deploying-to-render)
4. [Setting Up the Database](#setting-up-the-database)
5. [Configuring the Vet Desktop Application](#configuring-the-vet-desktop-application)
6. [Testing and Troubleshooting](#testing-and-troubleshooting)
7. [Maintenance and Monitoring](#maintenance-and-monitoring)

## Prerequisites

Before you begin, make sure you have:

- A [Render account](https://render.com/)
- Git installed on your computer
- Your ePetCare project code ready in a Git repository
- Basic knowledge of Django, PostgreSQL, and Python

## Preparing Your Application

1. **Set up your local environment for production deployment**

   The following files have been added to your project to prepare it for deployment:

   - `epetcare/settings_production.py`: Production settings for Django
   - `requirements.txt`: Dependencies required for deployment
   - `Procfile`: Instructions for Render on how to start your application
   - `render.yaml`: Configuration for Render services and database

2. **Update your existing application**

   We've added API endpoints for database synchronization in `vet_portal/api/views.py` and configured them in `vet_portal/api/urls.py`. We've also updated the desktop app to connect to these endpoints.

## Deploying to Render

1. **Create a new Web Service on Render**

   You can deploy the application in two ways:

   **Option 1: Use the Render Dashboard**
   
   - Log in to your Render account
   - Click "New +" and select "Blueprint"
   - Connect your repository
   - Render will automatically detect the `render.yaml` file and set up your services

   **Option 2: Deploy from your local machine**
   
   - Install the Render CLI (optional): `npm install -g @render/cli`
   - Run: `render blueprint up`
   - Follow the prompts

2. **Environment Variables**

   Ensure the following environment variables are set in your Render dashboard:

   - `SECRET_KEY`: Your Django secret key (auto-generated)
   - `DATABASE_URL`: Your PostgreSQL database URL (auto-connected)
   - `ALLOWED_HOST`: Your custom domain if you have one
   - `DJANGO_SETTINGS_MODULE`: Set to `epetcare.settings_production`

## Setting Up the Database

1. **Database Migration**

   After your application is deployed, you need to migrate your database:

   ```bash
   # Connect to your Render service shell
   $ render shell epetcare
   
   # Run migrations
   $ python manage.py migrate
   
   # Create a superuser
   $ python manage.py createsuperuser
   ```

2. **Migrating Data from SQLite to PostgreSQL**

   To migrate your existing data:

   ```bash
   # Export from SQLite (run locally)
   $ python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
   
   # Upload the file to your Render service
   
   # Import to PostgreSQL (on Render shell)
   $ python manage.py loaddata data.json
   ```

## Configuring the Vet Desktop Application

1. **Update the Desktop App Configuration**

   On each veterinarian's computer running the desktop app:

   - Open the `config.json` file
   - Update the `remote_database` section:

   ```json
   "remote_database": {
       "enabled": true,
       "url": "https://your-app-name.onrender.com",
       "username": "vet_username",
       "password": "vet_password",
       "sync_interval": 300,
       "auto_sync": true
   }
   ```

2. **Testing the Connection**

   - Start the vet desktop application
   - It should automatically connect to the remote database
   - Make a test appointment and verify it appears in both systems

## Testing and Troubleshooting

1. **Common Issues and Solutions**

   - **Database Connection Errors**: Ensure the `DATABASE_URL` is correctly set in Render dashboard
   - **500 Server Errors**: Check the Render logs for Python exceptions
   - **API Authentication Failures**: Verify user permissions and authentication tokens
   - **Sync Issues**: Check network connectivity and API endpoint responses

2. **Checking Logs on Render**

   - Go to your Render dashboard
   - Select your web service
   - Click on "Logs" to view application logs
   - Use log filters to focus on specific issues

## Maintenance and Monitoring

1. **Regular Database Backups**

   Render PostgreSQL databases are automatically backed up daily. Additionally:

   - Set up scheduled tasks for weekly backups to external storage
   - Test database restoration periodically

2. **Monitoring Application Health**

   - Set up monitoring in the Render dashboard
   - Configure alerts for service downtime
   - Monitor database performance metrics

3. **Updating Your Application**

   To deploy updates:

   ```bash
   # Push changes to your repository
   $ git add .
   $ git commit -m "Update application"
   $ git push
   
   # Render will automatically deploy changes
   ```

---

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

If you encounter any issues with your deployment, please refer to:

- Render Support: support@render.com
- Project Maintainer: your-email@example.com