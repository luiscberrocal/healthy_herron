"""
Comprehensive model tests for the fasting app.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from healthy_herron.fasting.models import Fast
from healthy_herron.fasting.tests.factories import FastFactory, UserFactory

User = get_user_model()


class FastModelTest(TestCase):
    """Test the Fast model."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    def test_fast_creation(self):
        """Test creating a new fast."""
        fast = Fast.objects.create(user=self.user, start_time=timezone.now())

        assert fast.user == self.user
        assert fast.start_time is not None
        assert fast.end_time is None
        assert fast.is_active

    def test_fast_string_representation(self):
        """Test the string representation of a fast."""
        start_time = timezone.now() - timedelta(hours=16)
        fast = FastFactory.create(
            user=self.user,
            start_time=start_time,
            end_time=timezone.now(),
            emotional_status="satisfied",
        )

        expected = f"Fast {start_time.strftime('%Y-%m-%d')} ({fast.duration_hours})"
        assert str(fast) == expected

    def test_is_active_property(self):
        """Test the is_active property."""
        # Active fast
        active_fast = Fast.objects.create(user=self.user, start_time=timezone.now())
        assert active_fast.is_active

        # Completed fast
        completed_fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status="satisfied",
        )
        assert not completed_fast.is_active

    def test_duration_property(self):
        """Test the duration property."""
        start_time = timezone.now() - timedelta(hours=16, minutes=30)
        end_time = timezone.now()

        fast = Fast.objects.create(
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            emotional_status="energized",
        )

        expected_duration = end_time - start_time
        assert fast.duration == expected_duration

    def test_duration_property_active_fast(self):
        """Test duration property for active fast returns None."""
        fast = Fast.objects.create(user=self.user, start_time=timezone.now())

        assert fast.duration is None

    def test_elapsed_time_property(self):
        """Test the elapsed_time property."""
        start_time = timezone.now() - timedelta(hours=5)
        fast = Fast.objects.create(user=self.user, start_time=start_time)

        elapsed = fast.elapsed_time
        assert elapsed.total_seconds() >= 5 * 3600  # At least 5 hours

    def test_duration_hours_formatting(self):
        """Test duration_hours property formatting."""
        start_time = timezone.now() - timedelta(hours=16, minutes=30)
        end_time = timezone.now()

        fast = Fast.objects.create(
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            emotional_status="challenging",
        )

        # Should be formatted as "16h 30m"
        assert "16h" in fast.duration_hours
        assert "30m" in fast.duration_hours

    def test_elapsed_hours_formatting(self):
        """Test elapsed_hours property formatting."""
        start_time = timezone.now() - timedelta(hours=8, minutes=45)
        fast = Fast.objects.create(user=self.user, start_time=start_time)

        # Should be formatted as "8h 45m" (approximately)
        assert "h" in fast.elapsed_hours
        assert "m" in fast.elapsed_hours

    def test_duration_seconds(self):
        """Test duration_seconds property."""
        start_time = timezone.now() - timedelta(hours=2)
        end_time = timezone.now()

        fast = Fast.objects.create(
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            emotional_status="satisfied",
        )

        expected_seconds = int((end_time - start_time).total_seconds())
        assert fast.duration_seconds == expected_seconds

    def test_elapsed_seconds(self):
        """Test elapsed_seconds property."""
        start_time = timezone.now() - timedelta(hours=3)
        fast = Fast.objects.create(user=self.user, start_time=start_time)

        elapsed_seconds = fast.elapsed_seconds
        assert elapsed_seconds >= 3 * 3600  # At least 3 hours

    def test_end_fast_method(self):
        """Test the end_fast method."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=12),
        )

        fast.end_fast("energized", "Felt great!")

        assert fast.end_time is not None
        assert fast.emotional_status == "energized"
        assert fast.comments == "Felt great!"
        assert not fast.is_active

    def test_end_fast_already_ended(self):
        """Test ending an already ended fast raises error."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=12),
            end_time=timezone.now(),
            emotional_status="satisfied",
        )

        with pytest.raises(ValidationError):
            fast.end_fast("energized", "Test comment")

    def test_get_absolute_url(self):
        """Test get_absolute_url method."""
        fast = Fast.objects.create(user=self.user, start_time=timezone.now())

        expected_url = f"/fasting/fasts/{fast.pk}/"
        assert fast.get_absolute_url() == expected_url

    def test_clean_validation_end_time_before_start_time(self):
        """Test validation that end_time must be after start_time."""
        start_time = timezone.now()
        end_time = start_time - timedelta(hours=1)  # End before start

        fast = Fast(
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            emotional_status="satisfied",
        )

        with pytest.raises(ValidationError):
            fast.clean()

    def test_clean_validation_comments_too_long(self):
        """Test validation that comments cannot exceed 128 characters."""
        fast = Fast(
            user=self.user,
            start_time=timezone.now(),
            comments="x" * 129,  # 129 characters
        )

        with pytest.raises(ValidationError):
            fast.clean()

    def test_clean_validation_emotional_status_required_with_end_time(self):
        """Test validation that emotional_status is required when end_time is set."""
        fast = Fast(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=8),
            end_time=timezone.now(),
            # Missing emotional_status
        )

        with pytest.raises(ValidationError):
            fast.clean()

    def test_clean_validation_multiple_active_fasts(self):
        """Test validation that user cannot have multiple active fasts."""
        # Create first active fast
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=2),
        )

        # Try to create second active fast
        second_fast = Fast(user=self.user, start_time=timezone.now())

        with pytest.raises(ValidationError):
            second_fast.clean()

    def test_multiple_active_fasts_different_users(self):
        """Test that different users can have active fasts simultaneously."""
        user2 = UserFactory()

        # Create active fast for first user
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=2),
        )

        # Create active fast for second user - should be valid
        fast2 = Fast(user=user2, start_time=timezone.now())

        try:
            fast2.clean()  # Should not raise ValidationError
        except ValidationError:
            self.fail(
                "Different users should be able to have active fasts simultaneously",
            )

    def test_save_calls_clean(self):
        """Test that save() calls clean() for validation."""
        start_time = timezone.now()
        end_time = start_time - timedelta(hours=1)  # Invalid: end before start

        fast = Fast(
            user=self.user,
            start_time=start_time,
            end_time=end_time,
            emotional_status="satisfied",
        )

        with pytest.raises(ValidationError):
            fast.save()

    def test_emotional_status_choices(self):
        """Test emotional status choices."""
        valid_statuses = ["energized", "satisfied", "challenging", "difficult"]

        for status in valid_statuses:
            fast = Fast.objects.create(
                user=self.user,
                start_time=timezone.now() - timedelta(hours=8),
                end_time=timezone.now(),
                emotional_status=status,
            )
            assert fast.emotional_status == status

    def test_timezone_methods_placeholder(self):
        """Test timezone conversion methods (placeholder implementation)."""
        Fast.objects.create(user=self.user, start_time=timezone.now())

        test_datetime = timezone.now()

        # These methods currently return the input unchanged (TODO implementation)
        result_to = Fast.to_user_timezone(test_datetime, self.user)
        result_from = Fast.from_user_timezone(test_datetime, self.user)

        assert result_to == test_datetime
        assert result_from == test_datetime


class FastManagerTest(TestCase):
    """Test the Fast model manager."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.other_user = UserFactory()

    def test_for_user_queryset(self):
        """Test for_user manager method."""
        # Create fasts for different users
        user_fast = Fast.objects.create(user=self.user, start_time=timezone.now())
        other_user_fast = Fast.objects.create(
            user=self.other_user,
            start_time=timezone.now(),
        )

        # Test filtering
        user_fasts = Fast.objects.for_user(self.user)

        assert user_fast in user_fasts
        assert other_user_fast not in user_fasts

    def test_active_for_user_queryset(self):
        """Test active_for_user manager method."""
        # Create active and completed fasts
        active_fast = Fast.objects.create(user=self.user, start_time=timezone.now())
        completed_fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status="satisfied",
        )

        active_fasts = Fast.objects.active_for_user(self.user)

        assert active_fast in active_fasts
        assert completed_fast not in active_fasts

    def test_completed_for_user_queryset(self):
        """Test completed_for_user manager method."""
        # Create active and completed fasts
        active_fast = Fast.objects.create(user=self.user, start_time=timezone.now())
        completed_fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status="satisfied",
        )

        completed_fasts = Fast.objects.completed_for_user(self.user)

        assert active_fast not in completed_fasts
        assert completed_fast in completed_fasts


class SessionManagerTest(TestCase):
    """Test the SessionManager utility."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    def test_set_and_get_active_fast(self):
        """Test setting and getting active fast from session."""
        # This would require a mock request object with session
        # For now, we'll test the model-level functionality
        fast = Fast.objects.create(user=self.user, start_time=timezone.now())

        # Test that we can retrieve the active fast
        active_fasts = Fast.objects.active_for_user(self.user)
        assert active_fasts.count() == 1
        assert active_fasts.first() == fast

    def test_multiple_active_fasts_prevention(self):
        """Test that SessionManager helps prevent multiple active fasts."""
        # Create one active fast
        Fast.objects.create(user=self.user, start_time=timezone.now())

        # Attempting to create another should fail validation
        fast2 = Fast(user=self.user, start_time=timezone.now())

        with pytest.raises(ValidationError):
            fast2.clean()
