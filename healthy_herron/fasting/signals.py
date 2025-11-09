from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm

from .models import Fast


@receiver(post_save, sender=Fast)
def assign_fast_permissions(sender, instance, created, **kwargs):
    """
    Assign object-level permissions to Fast owner when created.
    Ensures users can only access their own fast records.
    """
    if created:
        # Assign object-level permissions to the fast owner
        assign_perm('view_own_fast', instance.user, instance)
        assign_perm('change_own_fast', instance.user, instance)
        assign_perm('delete_own_fast', instance.user, instance)