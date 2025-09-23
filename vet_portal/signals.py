from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User, Group, Permission
from vet.models import Veterinarian


@receiver(post_save, sender=Veterinarian)
def assign_vet_permissions(sender, instance, created, **kwargs):
    """
    When a new Veterinarian is created, add them to the Veterinarians group
    and ensure they have the necessary permissions.
    """
    if created:
        # Get or create the Veterinarians group
        vet_group, created = Group.objects.get_or_create(name='Veterinarians')
        
        # Add the user to the Veterinarians group
        instance.user.groups.add(vet_group)
        
        # Set staff status for permission purposes
        if not instance.user.is_staff:
            instance.user.is_staff = True
            instance.user.save(update_fields=['is_staff'])


@receiver(post_delete, sender=Veterinarian)
def remove_vet_permissions(sender, instance, **kwargs):
    """
    When a Veterinarian is deleted, remove them from the Veterinarians group.
    """
    try:
        # Get the Veterinarians group
        vet_group = Group.objects.get(name='Veterinarians')
        
        # Remove the user from the Veterinarians group
        instance.user.groups.remove(vet_group)
        
        # If the user doesn't belong to any other groups requiring staff status,
        # remove their staff status
        if instance.user.groups.count() == 0:
            instance.user.is_staff = False
            instance.user.save(update_fields=['is_staff'])
    except Group.DoesNotExist:
        pass  # Group doesn't exist, nothing to do
