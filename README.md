# ePetCare

Django web app + PySide6 desktop client sharing the same PostgreSQL database (Render).

## Deploying to Render (Web)

Two ways to provide settings and env vars:

1. Use the Render dashboard (recommended if you already created a service):
   - Add environment variable `DATABASE_URL` with your Render Postgres External Database URL (ends with `.render.com`, include `sslmode=require`).
   - Ensure `SECRET_KEY` is set (auto-generated is fine).
   - Build Command: `chmod +x build.sh && ./build.sh`
   - Start Command: `gunicorn epetcare.wsgi:application --bind 0.0.0.0:$PORT --workers 4`
   - Optional: set `PYTHON_VERSION` (e.g., `3.13.4`).

2. Use `render.yaml` (Infrastructure as Code):
   - Create a new Render Blueprint from this repo. Render will create a web service and a Postgres database, and set `DATABASE_URL` from the DB connection.

If you see `Error: DATABASE_URL environment variable is required` at startup, it means the runtime environment variable isn’t set. Add it in Render → your service → Environment.

## Local development

- Create `.env` at repo root with `DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require`
- Install server deps: `pip install -r requirements.txt`
- Run: `python manage.py runserver`

## Desktop app

- Copy `vet_desktop_app/config.example.json` to `vet_desktop_app/config.json` and fill in your Render database credentials.
- The desktop app connects directly to the same Render Postgres.

## Security

- See `SECURITY.md`. Do not commit real secrets. Rotate DB password in Render if exposed.
