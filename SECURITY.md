# Security Checklist for ePetCare

This project now uses a single shared PostgreSQL database (Render) for both the Django website and the PySide6 desktop app. Follow these steps to keep credentials and data safe.

## 1) Keep secrets out of git
- Ensure the following are NOT committed:
  - `.env`, any `*.env` files
  - `vet_desktop_app/config.json`
  - local databases like `*.sqlite3`
  - logs and backups under `vet_desktop_app/logs/`, `vet_desktop_app/backups/`, and `vet_desktop_app/data/`
- A repo-level `.gitignore` has been added to enforce this.

## 2) Configure credentials via environment or config
- Django web app: set `DATABASE_URL` in the Render dashboard (Environment → Environment Variables). Do not hardcode in `settings.py`.
- Desktop app: set `vet_desktop_app/config.json` locally from `vet_desktop_app/config.example.json`. Do not commit the real file.
- Always use the External Database URL from Render (host looks like `dpg-xxx-<region>.a.<region>-postgres.render.com`).

## 3) Rotate credentials if exposed
- If a Render DB URL/password has ever been posted or committed, rotate the database password in Render:
  1. Render → PostgreSQL → Connections → Rotate Password.
  2. Update the `DATABASE_URL` in Render (web service) and in your local desktop `config.json`.
  3. Restart services or apps.

## 4) SSL and connectivity
- Use `sslmode=require` for hosted Postgres.
- Ensure the host has a domain suffix (not just an internal hostname).

## 5) Least privilege and access
- Prefer separate DB users for staging vs production if applicable.
- Limit network access with Render’s available controls.

## 6) Backups and logging
- Keep automated backups within the provider (Render) rather than exporting plaintext dumps into the repo.
- Logs should be rotated and kept out of version control.

## 7) Updates and patches
- Keep dependencies up to date (psycopg2, Django, PySide6). Apply security updates promptly.

## 8) Incident response quick steps
- Revoke/rotate the exposed credential.
- Invalidate any long-lived tokens using that DB (not currently used here).
- Review DB audit logs for suspicious activity if available.

For questions or to extend this checklist (e.g., adding role-based DB permissions), open an issue or contact the maintainer.
