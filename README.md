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

### Email delivery on Render (SendGrid/Resend)

This project supports HTTP email providers to avoid SMTP blocking on platforms:

- SendGrid (recommended for quick start with Single Sender)
- Resend (requires domain verification)

Set these environment variables in Render → your service → Environment:

- EMAIL_HTTP_PROVIDER=sendgrid (or `resend`)
- For SendGrid: SENDGRID_API_KEY=... and DEFAULT_FROM_EMAIL="Your Name <verified@example.com>"
   - The From must be a verified Sender Identity in SendGrid.
      - Either complete Single Sender Verification for that exact email address, or
      - Authenticate a domain and use an address on that domain.
- For Resend: RESEND_API_KEY=... and DEFAULT_FROM_EMAIL="Your Name <no-reply@yourverifieddomain.com>"
   - The domain in From must be verified in Resend.

Production settings will automatically prefer the HTTP provider and keep SMTP disabled to prevent 500s.

To test email in Render:

1) Open the Render Shell for your service
2) Run:

```
python manage.py send_test_email_provider you@example.com --from-email "Your Name <verified@example.com>"
```

The command will print the provider and effective From. If you see a 403 from SendGrid, your From isn’t verified yet.

### Improve deliverability (avoid spam)

To help messages land in Inbox, not Spam:

- Use a domain you control and authenticate it in your provider (SPF, DKIM, DMARC). Single Sender with free email domains (e.g., Gmail) often lands in spam.
- Align the From domain with the authenticated domain, e.g., `no-reply@yourdomain.com`.
- Keep subjects neutral and content concise; avoid excessive links/HTML.
- This project disables SendGrid click/open tracking for transactional emails to avoid link rewriting that can trigger spam filters.

## Local development

- Create `.env` at repo root with `DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require`
- Install server deps: `pip install -r requirements.txt`
- Run: `python manage.py runserver`

## Desktop app

- Copy `vet_desktop_app/config.example.json` to `vet_desktop_app/config.json` and fill in your Render database credentials.
- The desktop app connects directly to the same Render Postgres.

## Security

- See `SECURITY.md`. Do not commit real secrets. Rotate DB password in Render if exposed.
