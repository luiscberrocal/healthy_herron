import os
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import CharField, EmailField, ImageField, JSONField, OneToOneField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image

from healthy_herron.core.models import AuditableModel, TimeStampedModel

from .managers import UserManager


def validate_avatar_size(image):
    """Validate that avatar file is ≤2MB."""
    max_size = 2 * 1024 * 1024  # 2MB in bytes
    if image.size > max_size:
        raise ValidationError(_("Avatar file size must be ≤2MB."))


def validate_avatar_format(image):
    """Validate that avatar is JPEG or PNG."""
    try:
        img = Image.open(image)
        if img.format not in ["JPEG", "PNG"]:
            raise ValidationError(_("Avatar must be a JPEG or PNG file."))
    except Exception:
        raise ValidationError(_("Invalid image file."))
    finally:
        image.seek(0)  # Reset file pointer


class User(AbstractUser):
    """
    Default custom user model for Healthy Herron.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    # Timezone field for fasting app
    timezone = CharField(
        _("Timezone"),
        max_length=50,
        default="UTC",
        help_text=_("User's timezone for accurate fasting time tracking"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})


def avatar_upload_path(instance, filename):
    """Generate upload path for user avatar."""
    _, ext = os.path.splitext(filename)
    return f"avatars/user_{instance.user.id}/avatar{ext}"


class Profile(AuditableModel, TimeStampedModel):
    """User profile model with additional fields.

    Automatically created when a User is created and deleted when User is deleted.
    """

    user = OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("User"),
    )

    display_name = CharField(
        _("Display Name"),
        max_length=150,
        help_text=_("Display name with emoji support"),
    )

    avatar = ImageField(
        _("Avatar"),
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        validators=[validate_avatar_size, validate_avatar_format],
        help_text=_("Profile avatar image (JPEG/PNG, max 2MB)"),
    )

    configuration = JSONField(
        _("Configuration"),
        default=dict,
        blank=True,
        help_text=_("User configuration settings"),
    )

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        return f"{self.user.email} - {self.display_name}"

    def get_default_configuration(self):
        """Return default configuration for new profiles."""
        return {
            "fasting": {
                "min_fast_duration": 30,
                "max_fast_duration": 1440,
            },
        }

    def save(self, *args, **kwargs):
        """Override save to set default configuration if empty."""
        if not self.configuration:
            self.configuration = self.get_default_configuration()

        # Clean up old avatar when replacing
        if self.pk:
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.avatar and self.avatar != old_profile.avatar:
                    if default_storage.exists(old_profile.avatar.name):
                        default_storage.delete(old_profile.avatar.name)
            except Profile.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to clean up avatar file."""
        if self.avatar and default_storage.exists(self.avatar.name):
            default_storage.delete(self.avatar.name)
        super().delete(*args, **kwargs)

    def set_configuration(self, app_name: str, key: str, value: any):
        """Set a configuration value for a specific app and key.

        Args:
            app_name: Name of the app (e.g., 'fasting', 'nutrition')
            key: Configuration key within the app
            value: Value to set
        """
        if not self.configuration:
            self.configuration = {}

        if app_name not in self.configuration:
            self.configuration[app_name] = {}

        self.configuration[app_name][key] = value
        self.save()

    def delete_configuration(self, app_name: str, key: str | None = None):
        """Delete a configuration value or entire app configuration.

        Args:
            app_name: Name of the app
            key: Specific key to delete. If None, deletes entire app configuration
        """
        if not self.configuration or app_name not in self.configuration:
            return

        if key is None:
            # Delete entire app configuration
            del self.configuration[app_name]
        # Delete specific key
        elif key in self.configuration[app_name]:
            del self.configuration[app_name][key]

            # Clean up empty app configuration
            if not self.configuration[app_name]:
                del self.configuration[app_name]

        self.save()

    def get_configuration(self, app_name: str, key: str | None = None, default=None):
        """Get a configuration value.

        Args:
            app_name: Name of the app
            key: Specific key to get. If None, returns entire app configuration
            default: Default value if key/app not found

        Returns:
            Configuration value or default
        """
        if not self.configuration or app_name not in self.configuration:
            return default

        if key is None:
            return self.configuration[app_name]

        return self.configuration[app_name].get(key, default)
