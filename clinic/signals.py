from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Appointment, Prescription, MedicalRecord, Notification, Owner
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.conf import settings
from .utils.emailing import send_mail_http
from django.db import transaction

import logging
logger = logging.getLogger('clinic')
logger.info('[SIGNALS MODULE] clinic.signals module loaded - registering signal handlers')


# --- Appointment notifications ---

@receiver(pre_save, sender=Appointment)
def _capture_old_status(sender, instance: Appointment, **kwargs):
    """Store previous status on the instance for comparison in post_save."""
    if instance.pk:
        try:
            old = Appointment.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Appointment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Appointment)
def appointment_notify(sender, instance: Appointment, created: bool, **kwargs):
    """Create notifications for appointment changes. Never raises exceptions."""
    import logging
    logger = logging.getLogger('clinic')
    try:
        logger.info(f'[SIGNAL] appointment_notify triggered: created={created}, pet={instance.pet.name}, id={instance.id}')
        owner = instance.pet.owner
        logger.info(f'[SIGNAL] Owner found: {owner.full_name} (id={owner.id})')
        if created:
            notif = Notification.objects.create(
                owner=owner,
                appointment=instance,
                notif_type=Notification.Type.APPOINTMENT_CREATED,
                title="Appointment Scheduled",
                message=f"An appointment for {instance.pet.name} was scheduled on {instance.date_time:%b %d, %H:%M}.",
            )
            logger.info(f'[SIGNAL] Notification created successfully: id={notif.id}')
            return

        # Status change notifications
        old_status = getattr(instance, "_old_status", None)
        if old_status and old_status != instance.status:
            if instance.status == Appointment.Status.CANCELLED:
                Notification.objects.create(
                    owner=owner,
                    appointment=instance,
                    notif_type=Notification.Type.APPOINTMENT_CANCELLED,
                    title="Appointment Cancelled",
                    message=f"Your appointment for {instance.pet.name} on {instance.date_time:%b %d, %H:%M} was cancelled by the clinic.",
                )
            else:
                Notification.objects.create(
                    owner=owner,
                    appointment=instance,
                    notif_type=Notification.Type.APPOINTMENT_UPDATED,
                    title="Appointment Updated",
                    message=f"Your appointment for {instance.pet.name} was updated (status: {instance.get_status_display()}).",
                )
    except Exception as e:
        import logging
        logging.getLogger('clinic').error(f'Failed to create appointment notification: {e}', exc_info=True)


# --- Prescription notifications ---
@receiver(post_save, sender=Prescription)
def prescription_notify(sender, instance: Prescription, created: bool, **kwargs):
    """Create notifications for new prescriptions. Never raises exceptions."""
    import logging
    logger = logging.getLogger('clinic')
    try:
        logger.info(f'[SIGNAL] prescription_notify triggered: created={created}, pet={instance.pet.name}, medication={instance.medication_name}')
        if not created:
            logger.info('[SIGNAL] Prescription not new, skipping notification')
            return
        pet = instance.pet
        logger.info(f'[SIGNAL] Owner found: {pet.owner.full_name} (id={pet.owner.id})')
        notif = Notification.objects.create(
            owner=pet.owner,
            notif_type=Notification.Type.GENERAL,
            title="New Prescription",
            message=f"A new prescription for {pet.name} was added: {instance.medication_name} ({instance.dosage}).",
        )
        logger.info(f'[SIGNAL] Notification created successfully: id={notif.id}')
    except Exception as e:
        logger.error(f'Failed to create prescription notification: {e}', exc_info=True)


# --- Medical record notifications ---
@receiver(post_save, sender=MedicalRecord)
def medical_record_notify(sender, instance: MedicalRecord, created: bool, **kwargs):
    """Create notifications for new medical records. Never raises exceptions."""
    import logging
    logger = logging.getLogger('clinic')
    try:
        logger.info(f'[SIGNAL] medical_record_notify triggered: created={created}, pet={instance.pet.name}, condition={instance.condition}')
        if not created:
            logger.info('[SIGNAL] Medical record not new, skipping notification')
            return
        pet = instance.pet
        logger.info(f'[SIGNAL] Owner found: {pet.owner.full_name} (id={pet.owner.id})')
        notif = Notification.objects.create(
            owner=pet.owner,
            notif_type=Notification.Type.GENERAL,
            title="New Medical Record",
            message=f"A new medical record for {pet.name} was added: {instance.condition}.",
        )
        logger.info(f'[SIGNAL] Notification created successfully: id={notif.id}')
    except Exception as e:
        logger.error(f'Failed to create medical record notification: {e}', exc_info=True)


# --- Email owners when a Notification is created ---
@receiver(post_save, sender=Notification)
def email_owner_on_notification(sender, instance: Notification, created: bool, **kwargs):
    """Send email notification to owner. Never raises exceptions to avoid breaking request flow."""
    try:
        if not created:
            return
        owner = instance.owner
        # Resolve owner's email: prefer linked user.email, fallback to owner.email
        user_email = getattr(getattr(owner, 'user', None), 'email', '') or ''
        to_email = user_email or (owner.email or '')
        if not to_email:
            return
        subject = f"{getattr(settings, 'BRAND_NAME', 'ePetCare')}: {instance.title}"
        ctx = {
            'title': instance.title,
            'message': instance.message,
            'owner': owner,
            'created_at': instance.created_at,
            'BRAND_NAME': getattr(settings, 'BRAND_NAME', 'ePetCare'),
            'EMAIL_BRAND_LOGO_URL': getattr(settings, 'EMAIL_BRAND_LOGO_URL', ''),
        }
        # Text body
        try:
            text_body = render_to_string('clinic/notifications/email_notification.txt', ctx)
        except Exception:
            # Fallback to a simple text if template missing
            text_body = f"{instance.title}\n\n{instance.message}\n\n— {getattr(settings, 'BRAND_NAME', 'ePetCare')}"
        # HTML body (optional)
        try:
            html_body = render_to_string('clinic/notifications/email_notification.html', ctx)
        except Exception:
            html_body = None
        try:
            success = send_mail_http(subject, text_body, [to_email], settings.DEFAULT_FROM_EMAIL, html_message=html_body)
            if success:
                # Mark as emailed to avoid duplicate sends on replay
                def _mark_emailed():
                    try:
                        Notification.objects.filter(pk=instance.pk, emailed=False).update(emailed=True)
                    except Exception:
                        pass
                # Ensure DB commit before update in transaction contexts
                if transaction.get_connection().in_atomic_block:
                    transaction.on_commit(_mark_emailed)
                else:
                    _mark_emailed()
        except Exception as mail_err:
            # Don't break request flow if emailing fails
            logger.error(f'Failed to send notification email: {mail_err}')
    except Exception as e:
        # Catch any unexpected exception to prevent 500 errors
        import logging
        logging.getLogger('clinic').error(f'Failed to send notification email: {e}', exc_info=True)
        pass


# --- Keep Owner.email synchronized with User.email ---
@receiver(post_save, sender=User)
def sync_owner_email(sender, instance: User, **kwargs):
    try:
        owner = getattr(instance, 'owner_profile', None)
        if owner and owner.email != instance.email:
            owner.email = instance.email or ''
            owner.save(update_fields=['email'])
    except Exception:
        # Do not interrupt auth flows if there is no owner or save fails
        pass


@receiver(post_save, sender=Owner)
def sync_user_email(sender, instance: Owner, **kwargs):
    try:
        user = instance.user
        if user and (user.email or '') != (instance.email or ''):
            user.email = instance.email or ''
            user.save(update_fields=['email'])
    except Exception:
        # Avoid breaking owner updates if the user cannot be updated
        pass


# Log that all signal handlers have been registered
logger.info('[SIGNALS MODULE] All signal handlers registered: appointment_notify, prescription_notify, medical_record_notify, email_owner_on_notification, sync_owner_email, sync_user_email')
