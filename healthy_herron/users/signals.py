"""User-related signals."""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile instance when a User is created."""
    if created:
        Profile.objects.create(
            user=instance,
            display_name=instance.name or instance.email.split("@")[0],
            created_by=instance,
            modified_by=instance,
        )


@receiver(post_delete, sender=User)
def delete_user_profile_avatar(sender, instance, **kwargs):
    """Clean up avatar when user is deleted."""
    try:
        profile = instance.profile
        if profile.avatar:
            profile.delete()  # This will trigger Profile.delete() which cleans up the avatar
    except Profile.DoesNotExist:
        pass
