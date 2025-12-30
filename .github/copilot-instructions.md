# ePetCare Copilot Instructions

## Architecture Overview

ePetCare is a **hybrid system**: Django web app + PySide6 desktop app sharing the same PostgreSQL database.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL (Render)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   Django Web          Django Web          PySide6 Desktop
   (clinic app)        (vet/vet_portal)    (vet_desktop_app)
   Pet Owners          Veterinarians       Superadmin/Vets
```

### Django Apps
- **`clinic/`** - Pet owner portal: pets, appointments, notifications, OTP password reset
- **`vet/`** - Veterinarian web portal with dashboard layout
- **`vet_portal/`** - DRF API + additional vet views; syncs with desktop app

### Desktop App
- **`vet_desktop_app/`** - PySide6 Qt app for vets/superadmin
- Connects **directly to PostgreSQL** (no Django ORM at runtime)
- Uses `utils/password_hasher.py` for Django-compatible PBKDF2 hashing

## Key Patterns

### User Profiles (OneToOne relationships)
```python
# Pet owners: User -> Owner (clinic/models.py)
user.owner_profile  # Access owner from user

# Veterinarians: User -> Veterinarian (vet/models.py)
user.vet_profile    # Access vet from user
```

### Notifications System
- Created via Django signals in `clinic/signals.py` on model changes
- Desktop app writes directly to DB → Postgres triggers create notifications
- Emails sent immediately or via catch-up: `python manage.py send_pending_notifications`

### Template Inheritance
- **Pet owner dashboard**: extends `clinic/dashboard_base.html`
- **Vet portal**: extends `vet/base.html`
- **Auth pages**: extends `clinic/base_auth.html` (login, register, password reset)

### CSS Design Tokens
```css
/* Pet owner (clinic/dashboard_base.html) */
--owner-primary: #d48b3e;
--owner-bg: #FFF5E9;

/* Vet portal (vet/base.html) */
--vet-primary: #6b705c;
--vet-accent: #cb997e;
```

## Commands

```bash
# Run dev server
python manage.py runserver

# Check Django config
python manage.py check

# Send pending notification emails
python manage.py send_pending_notifications

# Test email provider (SendGrid/Brevo)
python manage.py send_test_email_provider you@example.com

# Run desktop app
cd vet_desktop_app && python main.py
```

## Settings Structure

- `config/settings/base.py` - Shared settings
- `config/settings/dev.py` - Local development (DEBUG=True)
- `config/settings/prod.py` - Production (Render)
- Set `DJANGO_SETTINGS_MODULE=config.settings.dev` for local work

## Desktop App Specifics

**Never import Django ORM in desktop app** - it doesn't have Django configured.

```python
# ✓ CORRECT - Use custom password hasher
from utils.password_hasher import make_password, verify_password

# ✗ WRONG - Will fail with "settings not configured"
from django.contrib.auth.hashers import make_password
```

Database access via `models/data_access.py` using raw SQL with psycopg2.

## File Locations

| Purpose | Location |
|---------|----------|
| Pet owner models | `clinic/models.py` |
| Vet models | `vet/models.py` |
| API serializers | `vet_portal/api/serializers.py` |
| Email utilities | `clinic/utils/emailing.py` |
| Desktop data access | `vet_desktop_app/models/data_access.py` |
| Auth templates | `clinic/templates/clinic/auth/` |

## Common Gotchas

1. **Profile dropdowns** - Use `!important` overrides due to conflicting styles in `modern.css`
2. **Email sending** - Uses HTTP providers (SendGrid/Brevo), not SMTP
3. **Password hashing** - Desktop uses `utils/password_hasher.py`, not Django's hasher
4. **Notifications** - Desktop creates need DB triggers or catch-up job for emails
