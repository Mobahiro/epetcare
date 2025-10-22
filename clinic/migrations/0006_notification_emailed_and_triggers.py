from django.db import migrations, models
from django.conf import settings


TRIGGER_SQL = r"""
-- Create function to insert notification for prescription
CREATE OR REPLACE FUNCTION clinic_notify_prescription() RETURNS trigger AS $$
DECLARE
    owner_id INTEGER;
    pet_name TEXT;
BEGIN
    SELECT p.owner_id, p.name INTO owner_id, pet_name FROM clinic_pet p WHERE p.id = NEW.pet_id;
    IF owner_id IS NOT NULL THEN
        INSERT INTO clinic_notification (owner_id, notif_type, title, message, is_read, emailed, created_at)
        VALUES (
            owner_id,
            'general',
            'New Prescription',
            CONCAT('A new prescription for ', pet_name, ' was added: ', NEW.medication_name, ' (', NEW.dosage, ').'),
            FALSE,
            FALSE,
            NOW()
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate trigger for prescription insert
DROP TRIGGER IF EXISTS trg_clinic_prescription_notify ON clinic_prescription;
CREATE TRIGGER trg_clinic_prescription_notify
AFTER INSERT ON clinic_prescription
FOR EACH ROW EXECUTE FUNCTION clinic_notify_prescription();

-- Create function to insert notification for medical record
CREATE OR REPLACE FUNCTION clinic_notify_medicalrecord() RETURNS trigger AS $$
DECLARE
    owner_id INTEGER;
    pet_name TEXT;
BEGIN
    SELECT p.owner_id, p.name INTO owner_id, pet_name FROM clinic_pet p WHERE p.id = NEW.pet_id;
    IF owner_id IS NOT NULL THEN
        INSERT INTO clinic_notification (owner_id, notif_type, title, message, is_read, emailed, created_at)
        VALUES (
            owner_id,
            'general',
            'New Medical Record',
            CONCAT('A new medical record for ', pet_name, ' was added: ', NEW.condition, '.'),
            FALSE,
            FALSE,
            NOW()
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate trigger for medical record insert
DROP TRIGGER IF EXISTS trg_clinic_medicalrecord_notify ON clinic_medicalrecord;
CREATE TRIGGER trg_clinic_medicalrecord_notify
AFTER INSERT ON clinic_medicalrecord
FOR EACH ROW EXECUTE FUNCTION clinic_notify_medicalrecord();
"""


def create_triggers(apps, schema_editor):
    # Only run for PostgreSQL
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(TRIGGER_SQL)


def drop_triggers(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
        DROP TRIGGER IF EXISTS trg_clinic_prescription_notify ON clinic_prescription;
        DROP FUNCTION IF EXISTS clinic_notify_prescription();
        DROP TRIGGER IF EXISTS trg_clinic_medicalrecord_notify ON clinic_medicalrecord;
        DROP FUNCTION IF EXISTS clinic_notify_medicalrecord();
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0005_passwordresetotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='emailed',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(create_triggers, reverse_code=drop_triggers),
    ]
