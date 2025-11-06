# ePetCare

Django web app + PySide6 desktop client sharing the same PostgreSQL database (Render).

This README includes a system analysis for Data Flow Diagrams (DFD) and backend flow understanding, plus deployment notes.

## System Overview (for DFD)

- Web: Django (apps: `clinic`, `vet`, `vet_portal`) with PostgreSQL.
- Desktop: PySide6 Vet Desktop app (`vet_desktop_app`) that connects to the same PostgreSQL.
- Email: SendGrid/Resend via HTTP API (SMTP fallback optional).
- Deployment: Render (Procfile, render.yaml, WhiteNoise).

### Core User Roles
- Pet Owner (Clinic web)
- Veterinarian (Vet/Vet Portal web)
- Veterinarian (Desktop app)

---

## Features (All)

### Pet Owner (Clinic)
- Register/login, profile and password change.
- Password reset with OTP (email-based, 3 steps).
- Pets: create, edit, delete, view.
- Appointments: schedule and view upcoming.
- Notifications: in-app list, unread count; email notifications for events.

### Veterinarian (Vet / Vet Portal web)
- Login/register (vet side).
- Dashboard: counts, upcoming appointments, latest notifications.
- Patients: list/search pets with owner info.
- Medical Records: create/edit/delete.
- Prescriptions: create/edit/delete.
- Appointments: list and manage.
- Notifications: list and mark read.

### Veterinarian (Desktop app)
- Login (Django-compatible PBKDF2 hashing).
- Dashboard with quick actions; today’s schedule.
- Patients/appointments views; create/update appointments.
- Backup utility (Postgres export).
- Notification monitor for new appointments (polling signal updates).

### Cross-cutting
- Email sending (HTTP provider first, SMTP fallback disabled in prod): HTML + text templates; tracking disabled; transactional categories.
- Notifications persisted to DB; emailed on create (signals) or via catch-up job.
- Postgres triggers ensure Notification rows for inserts done outside Django (e.g., by desktop) for Medical Records and Prescriptions.
- Management commands: `send_pending_notifications`, `send_test_otp`, `send_test_email_provider`, `check_deploy`, `reset_epetcare_data`.

---

## Modules and APIs Used

### Django apps
- `clinic/`
   - Models: `Owner`, `Pet`, `Appointment`, `Vaccination`, `MedicalRecord`, `Prescription`, `PasswordResetOTP`, `Notification`.
   - Views: owner dashboard, pets/appointments CRUD, OTP flow, notifications endpoints.
   - Forms: owner/pet/appointment forms, register, OTP forms.
   - Signals: create `Notification` rows and send emails on create/update; Owner/User sync.
   - Utils: `utils/emailing.py` (SendGrid/Resend/SMTP), `utils/notifications.py` (process unsent).
   - Management: `send_pending_notifications`, `send_test_otp`, `send_test_email_provider`, `check_deploy`, `reset_epetcare_data`.
- `vet/`
   - Models: `Veterinarian`, `VetNotification`.
   - Views: dashboard, patients, appointments, notifications, auth helpers.
   - URLs: `vet/urls.py` (home, register, login, logout, etc.).
- `vet_portal/`
   - API (Django REST Framework): ViewSets for Owners, Pets, Appointments, MedicalRecords, Prescriptions, Treatments, TreatmentRecords, VetSchedules; read-only VetNotifications; offline sync endpoints; mark read.
   - Views: dashboard, patients, records UI for vets; auth views.

### Desktop app (`vet_desktop_app/`)
- Views: `main_window.py`, `dashboard_view.py`, `patients_view.py`, `appointments_view.py`, `appointment_dialog.py`, `settings_view.py`.
- Models: `models.py` (dataclasses mirroring Django).
- Data access: `models/data_access.py` (SQL to PostgreSQL; appointment status stored as string).
- Utils: `pg_db.py`, `database.py`, `config.py`, `db_sync.py`, `notification_manager.py`.

### External APIs/Services
- SendGrid (HTTP API) / Resend (HTTP API) for email.
- Render PostgreSQL for database hosting.

---

## Backend Flows (How it works)

### Owner: Register/Login
1) User submits form → Django Auth checks `auth_user` (PBKDF2).
2) On success: session created; owner dashboard loads.

### Owner: Add/Edit Pet
1) Owner fills `PetCreateForm`/`PetForm` → view validates and saves to `clinic_pet`.
2) Owner redirected to pet detail/list; no email by default.

### Owner/Vet: Schedule Appointment
1) Owner (Clinic) or Vet (web/desktop) submits appointment.
2) Row written to `clinic_appointment` with `status` (e.g., `scheduled`).
3) Django signals (if action in web) create `Notification` for the owner; if created outside Django (desktop), DB triggers cover other models (prescription/record) and catch-up email job runs on owner dashboard/notifications or via `send_pending_notifications`.
4) Email sender composes HTML/text template and sends via HTTP provider; `Notification.emailed` set on success.

### Vet: Medical Record / Prescription
1) Vet creates/updates record.
2) Signal creates `Notification` to owner; DB triggers also insert Notification if record created outside Django.
3) Email pipeline same as above.

### Owner: Password Reset (OTP)
1) Request: generate 6-digit OTP in `PasswordResetOTP` with expiry; send email.
2) Verify: check OTP; set session guard for reset.
3) Set new password via `SetPasswordForm` → updates `auth_user`.

### Notifications Emailing
- On create: signal tries to send email immediately.
- Catch-up: `process_unsent_notifications` on owner dashboard/notifications; or `python manage.py send_pending_notifications`.

---

## DFD Text Guide (No diagrams)

Use the bullets below to draw your own DFDs.

### Level 0 – Context
- External Entities: Pet Owner, Veterinarian (Web), Veterinarian (Desktop), Email Provider (SendGrid/Resend), PostgreSQL (Render).
- System: ePetCare (Django + Desktop).
- Data Flows:
   - Pet Owner ↔ ePetCare (login, pets, appointments, notifications, OTP).
   - Veterinarian (Web) ↔ ePetCare (patients, appointments, records, prescriptions, notifications).
   - Veterinarian (Desktop) ↔ ePetCare (appointments, patients, backup; direct DB CRUD).
   - ePetCare ↔ Email Provider (send OTP and notification emails).
   - ePetCare ↔ PostgreSQL (all reads/writes).

### Level 1 – Major Processes and Stores
- Processes:
   - P1 Authentication (login/register)
   - P2 Pet Management (create/edit pet)
   - P3 Appointments (create/update)
   - P4 Medical Records & Prescriptions (create/update)
   - P5 Notifications & Email (create notification, send email, catch-up)
   - P6 Password Reset (OTP request/verify/set)
- Data Stores:
   - DS1 Owners/Pets (clinic_owner, clinic_pet)
   - DS2 Appointments (clinic_appointment)
   - DS3 Medical Records (clinic_medicalrecord)
   - DS4 Prescriptions (clinic_prescription)
   - DS5 Notifications (clinic_notification)
   - DS6 Users (auth_user)
   - DS7 OTP (clinic_passwordresetotp)
- Data Flows:
   - Owner → P1 → DS6; Owner ↔ session
   - Owner → P2 → DS1
   - Owner → P3 → DS2
   - Vet(Web) → P3 → DS2; Vet(Web) → P4 → DS3/DS4
   - Vet(Desktop) → P3 → DS2 (direct DB)
   - P3/P4 → P5 (Notification) → DS5 → Email Provider (send)
   - Owner → P6 → DS7 → Email Provider (OTP); P6 → DS6 (set new password)

### Level 2 – Pet Owner
- Dashboard: shows pets, upcoming appointments, notifications (reads DS1, DS2, DS5).
- Add/Edit Pet:
   - Input: pet details from owner.
   - Process: validate + save to DS1.
   - Output: confirmation/UI update.
- Schedule Appointment:
   - Input: pet, date/time, reason.
   - Process: save to DS2; create notification in DS5; email may be sent; if not, catch-up job later.
   - Output: appointment visible to owner; email received if configured.
- View Notifications:
   - Input: owner request.
   - Process: read DS5; mark read.
- Password Reset (OTP):
   - Step 1: request generates OTP in DS7; email sent via provider.
   - Step 2: verify OTP against DS7; set session guard.
   - Step 3: set new password in DS6.

### Level 2 – Veterinarian (Web & Desktop)
- Patients:
   - Read DS1 to list pets with owners; view details.
- Create/Update Appointment:
   - Input: pet, date/time, reason, status.
   - Web path: Django view saves to DS2; signal creates notification in DS5; email sender runs.
   - Desktop path: direct write to DS2; notifications emailed via Django catch-up when owner hits dashboard/notifications or via command.
- Medical Record / Prescription:
   - Input: visit data/medication.
   - Web path: save to DS3/DS4; signal creates notification DS5; email.
   - Outside Django: Postgres triggers insert notifications, then email via catch-up.
- Notifications:
   - Read DS5; mark read via web.
- Backup (Desktop):
   - Calls pg backup utility; no app DB changes.

## System Flowchart Guidance (Plain text)

### Schedule Appointment (Owner/Vet)
1) Open create appointment form.
2) Validate inputs (pet, date/time, reason).
3) Insert/Update row in DS2 (clinic_appointment).
4) Create notification in DS5 (signal/trigger).
5) Attempt to send email via provider.
6) If success, mark notification emailed=True; otherwise leave for catch-up sender.

### Password Reset (OTP)
1) Submit email/username.
2) Create OTP in DS7 with expiry.
3) Send OTP email.
4) Enter OTP; verify against DS7 and expiry.
5) If valid, allow new password form.
6) Update password in DS6 (auth_user).

---

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
