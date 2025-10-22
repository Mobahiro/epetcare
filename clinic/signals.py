from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Appointment, Prescription, MedicalRecord, Notification, Owner
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.conf import settings
from .utils.emailing import send_mail_async_safe
from django.db import transaction


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
    owner = instance.pet.owner
    if created:
        Notification.objects.create(
            owner=owner,
            appointment=instance,
            notif_type=Notification.Type.APPOINTMENT_CREATED,
            title="Appointment Scheduled",
            message=f"An appointment for {instance.pet.name} was scheduled on {instance.date_time:%b %d, %H:%M}.",
        )
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


# --- Prescription notifications ---
@receiver(post_save, sender=Prescription)
def prescription_notify(sender, instance: Prescription, created: bool, **kwargs):
    if not created:
        return
    pet = instance.pet
    Notification.objects.create(
        owner=pet.owner,
        notif_type=Notification.Type.GENERAL,
        title="New Prescription",
        message=f"A new prescription for {pet.name} was added: {instance.medication_name} ({instance.dosage}).",
    )


# --- Medical record notifications ---
@receiver(post_save, sender=MedicalRecord)
def medical_record_notify(sender, instance: MedicalRecord, created: bool, **kwargs):
    if not created:
        return
    pet = instance.pet
    Notification.objects.create(
        owner=pet.owner,
        notif_type=Notification.Type.GENERAL,
        title="New Medical Record",
        message=f"A new medical record for {pet.name} was added: {instance.condition}.",
    )


# --- Email owners when a Notification is created ---
@receiver(post_save, sender=Notification)
def email_owner_on_notification(sender, instance: Notification, created: bool, **kwargs):
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
        send_mail_async_safe(subject, text_body, [to_email], html_message=html_body)
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
    except Exception:
        # Don't break request flow if emailing fails
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
