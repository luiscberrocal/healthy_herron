from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from healthy_herron.core.models import AuditableModel

User = get_user_model()


class FastManager(models.Manager):
    """Custom manager for Fast model with user filtering and concurrency control."""

    def for_user(self, user):
        """Return fasts belonging to specific user."""
        return self.filter(user=user)

    def active_for_user(self, user):
        """Return active (unfinished) fasts for user."""
        return self.filter(user=user, end_time__isnull=True)

    def completed_for_user(self, user):
        """Return completed fasts for user."""
        return self.filter(user=user, end_time__isnull=False)

    def with_lock(self):
        """Apply database-level locking for concurrent operations."""
        return self.select_for_update()


class Fast(AuditableModel, TimeStampedModel):
    """
    Represents a single fasting period with start time, optional end time,
    emotional status, and user comments.
    """

    EMOTIONAL_STATUS_CHOICES = [
        ("energized", _("Energized")),
        ("satisfied", _("Satisfied")),
        ("challenging", _("Challenging")),
        ("difficult", _("Difficult")),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("Owner of the fast record"),
        db_index=True,
    )
    start_time = models.DateTimeField(
        verbose_name=_("Start Time"),
        help_text=_("When the fast began"),
        default=timezone.now,
    )
    end_time = models.DateTimeField(
        verbose_name=_("End Time"),
        help_text=_("When the fast ended"),
        null=True,
        blank=True,
    )
    emotional_status = models.CharField(
        max_length=20,
        choices=EMOTIONAL_STATUS_CHOICES,
        verbose_name=_("Emotional Status"),
        help_text=_("User's emotional state when ending fast"),
        null=True,
        blank=True,
    )
    comments = models.TextField(
        max_length=128,
        verbose_name=_("Comments"),
        help_text=_("User's reflection on the fast (max 128 characters)"),
        blank=True,
    )

    objects = FastManager()

    class Meta:
        ordering = ["-start_time"]  # Most recent first (FR-015)
        indexes = [
            models.Index(fields=["user", "-start_time"]),
            models.Index(fields=["user", "end_time"]),
        ]
        permissions = [
            ("view_own_fast", "Can view own fasting records"),
            ("change_own_fast", "Can change own fasting records"),
            ("delete_own_fast", "Can delete own fasting records"),
        ]
        verbose_name = _("Fast")
        verbose_name_plural = _("Fasts")

    def __str__(self):
        """String representation for admin and debugging."""
        if self.is_active:
            return f"Active fast started {self.start_time.strftime('%Y-%m-%d %H:%M')}"
        return f"Fast {self.start_time.strftime('%Y-%m-%d')} ({self.duration_hours})"

    def clean(self):
        """Validate model constraints."""
        super().clean()

        # Validate end_time is after start_time if provided (FR-016)
        if self.end_time and self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time."))

        # Validate comments length (FR-019)
        if self.comments and len(self.comments) > 128:
            raise ValidationError(_("Comments cannot exceed 128 characters."))

        # Validate emotional_status is required when end_time is set (FR-007)
        if self.end_time and not self.emotional_status:
            raise ValidationError(_("Emotional status is required when ending a fast."))

        # Validate user cannot have multiple active fasts (FR-003)
        if not self.end_time:  # This is an active fast
            existing_active = Fast.objects.active_for_user(self.user)
            if self.pk:  # Exclude self if updating
                existing_active = existing_active.exclude(pk=self.pk)
            if existing_active.exists():
                raise ValidationError(_("You can only have one active fast at a time."))

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Boolean indicating if fast is ongoing (end_time is None)."""
        return self.end_time is None

    @property
    def duration(self):
        """Calculated duration for completed fasts (end_time - start_time)."""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def elapsed_time(self):
        """Time elapsed from start_time to now (for active fasts)."""
        return timezone.now() - self.start_time

    @property
    def duration_hours(self):
        """Duration formatted in hours and minutes."""
        if self.duration:
            total_seconds = int(self.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return ""

    @property
    def elapsed_hours(self):
        """Elapsed time formatted in hours and minutes."""
        total_seconds = int(self.elapsed_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    @property
    def duration_seconds(self):
        """Total duration in seconds for HTMX updates."""
        if self.duration:
            return int(self.duration.total_seconds())
        return 0

    @property
    def elapsed_seconds(self):
        """Total elapsed time in seconds for HTMX updates."""
        return int(self.elapsed_time.total_seconds())

    def end_fast(self, emotional_status, comments=""):
        """Complete the fast with emotional status."""
        if self.end_time:
            raise ValidationError(_("Fast is already completed."))

        self.end_time = timezone.now()
        self.emotional_status = emotional_status
        self.comments = comments
        self.save()

    def get_absolute_url(self):
        """URL to fast detail view."""
        return reverse("fasting:fast_detail", kwargs={"pk": self.pk})

    @staticmethod
    def to_user_timezone(dt, user):
        """Convert datetime to user's configured timezone."""
        # TODO: Implement when user timezone field is added
        return dt

    @staticmethod
    def from_user_timezone(dt, user):
        """Convert datetime from user's timezone to UTC."""
        # TODO: Implement when user timezone field is added
        return dt


class SessionManager:
    """
    Session management utilities for handling user fast state and concurrency.
    Provides session-level locking and state management for fast operations.
    """

    @staticmethod
    def get_user_active_fast(request):
        """Get the active fast for the current user from session or database."""
        if not request.user.is_authenticated:
            return None

        # Check session cache first
        active_fast_id = request.session.get("active_fast_id")
        if active_fast_id:
            try:
                return Fast.objects.get(
                    id=active_fast_id,
                    user=request.user,
                    end_time__isnull=True,
                )
            except Fast.DoesNotExist:
                # Clear invalid session data
                del request.session["active_fast_id"]

        # Fallback to database query
        try:
            fast = Fast.objects.active_for_user(request.user).first()
            if fast:
                request.session["active_fast_id"] = fast.id
            return fast
        except Fast.DoesNotExist:
            return None

    @staticmethod
    def set_active_fast(request, fast):
        """Set the active fast in the user's session."""
        if fast and fast.is_active:
            request.session["active_fast_id"] = fast.id
        else:
            request.session.pop("active_fast_id", None)

    @staticmethod
    def clear_active_fast(request):
        """Clear the active fast from the user's session."""
        request.session.pop("active_fast_id", None)

    @staticmethod
    def acquire_fast_lock(user, fast_id=None):
        """
        Acquire database-level lock for fast operations to prevent concurrency issues.
        Returns the locked Fast instance or None if lock cannot be acquired.
        """
        try:
            if fast_id:
                return Fast.objects.with_lock().get(id=fast_id, user=user)
            # Lock active fast for user
            return (
                Fast.objects.with_lock()
                .filter(user=user, end_time__isnull=True)
                .first()
            )
        except Fast.DoesNotExist:
            return None
