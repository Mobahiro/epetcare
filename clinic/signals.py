from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Appointment, Prescription, MedicalRecord, Notification


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
