"""
Comprehensive form tests for the fasting app.
"""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from healthy_herron.fasting.forms import EndFastForm, StartFastForm
from healthy_herron.fasting.models import Fast
from healthy_herron.fasting.tests.factories import FastFactory, UserFactory


class FastFormTest(TestCase):
    """Test the FastForm for starting new fasts."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    def test_fast_form_valid_data(self):
        """Test form with valid data."""
        form_data = {"start_time": timezone.now() - timedelta(hours=1)}
        form = StartFastForm(data=form_data, user=self.user)

        assert form.is_valid()

    def test_fast_form_future_start_time(self):
        """Test form with future start time."""
        form_data = {"start_time": timezone.now() + timedelta(hours=1)}
        form = StartFastForm(data=form_data, user=self.user)

        assert not form.is_valid()
        assert "start_time" in form.errors
        assert "cannot be in the future" in str(form.errors["start_time"])

    def test_fast_form_with_existing_active_fast(self):
        """Test form when user already has an active fast."""
        # Create existing active fast
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=5),
        )

        form_data = {"start_time": timezone.now() - timedelta(hours=1)}
        form = StartFastForm(data=form_data, user=self.user)

        assert not form.is_valid()
        assert "__all__" in form.errors
        assert "already have an active fast" in str(form.errors["__all__"])

    def test_fast_form_missing_start_time(self):
        """Test form with missing start time."""
        form_data = {}
        form = StartFastForm(data=form_data, user=self.user)

        assert not form.is_valid()
        assert "start_time" in form.errors

    def test_fast_form_invalid_start_time_format(self):
        """Test form with invalid start time format."""
        form_data = {"start_time": "invalid-date"}
        form = StartFastForm(data=form_data, user=self.user)

        assert not form.is_valid()
        assert "start_time" in form.errors

    def test_fast_form_save(self):
        """Test form save method."""
        form_data = {"start_time": timezone.now() - timedelta(hours=2)}
        form = StartFastForm(data=form_data, user=self.user)

        assert form.is_valid()

        fast = form.save()

        assert isinstance(fast, Fast)
        assert fast.user == self.user
        assert fast.start_time == form_data["start_time"]
        assert fast.end_time is None
        assert fast.emotional_status is None

    def test_fast_form_widget_attributes(self):
        """Test form widget attributes for proper rendering."""
        form = StartFastForm(user=self.user)

        start_time_widget = form.fields["start_time"].widget
        assert start_time_widget.input_type == "datetime-local"
        assert "class" in start_time_widget.attrs

    def test_fast_form_help_text(self):
        """Test form help text."""
        form = StartFastForm(user=self.user)

        help_text = form.fields["start_time"].help_text
        assert "When the fast began" in help_text

    def test_fast_form_label(self):
        """Test form field labels."""
        form = StartFastForm(user=self.user)

        assert form.fields["start_time"].label == "Start Time"


class EndFastFormTest(TestCase):
    """Test the EndFastForm for ending active fasts."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
        )

    def test_end_fast_form_valid_data(self):
        """Test form with valid data."""
        form_data = {
            "end_time": timezone.now(),
            "emotional_status": "energized",
            "comments": "Felt great during this fast!",
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        assert form.is_valid()

    def test_end_fast_form_minimal_valid_data(self):
        """Test form with minimal required data."""
        form_data = {"end_time": timezone.now(), "emotional_status": "satisfied"}
        form = EndFastForm(data=form_data, instance=self.fast)

        assert form.is_valid()

    def test_end_fast_form_missing_emotional_status(self):
        """Test form with missing emotional status."""
        form_data = {"end_time": timezone.now(), "comments": "Test comment"}
        form = EndFastForm(data=form_data, instance=self.fast)

        assert not form.is_valid()
        assert "emotional_status" in form.errors

    def test_end_fast_form_missing_end_time(self):
        """Test form with missing end time."""
        form_data = {"emotional_status": "satisfied", "comments": "Test comment"}
        form = EndFastForm(data=form_data, instance=self.fast)

        assert not form.is_valid()
        assert "end_time" in form.errors

    def test_end_fast_form_end_time_before_start_time(self):
        """Test form with end time before start time."""
        form_data = {
            "end_time": self.fast.start_time - timedelta(hours=1),
            "emotional_status": "satisfied",
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        assert not form.is_valid()
        assert "end_time" in form.errors
        assert "End time must be after the start time." in str(form.errors["end_time"])

    def test_end_fast_form_invalid_emotional_status(self):
        """Test form with invalid emotional status."""
        form_data = {"end_time": timezone.now(), "emotional_status": "invalid_status"}
        form = EndFastForm(data=form_data, instance=self.fast)

        assert not form.is_valid()
        assert "emotional_status" in form.errors

    def test_end_fast_form_valid_emotional_statuses(self):
        """Test form with all valid emotional statuses."""
        valid_statuses = [status[0] for status in Fast.EMOTIONAL_STATUS_CHOICES]

        for status in valid_statuses:
            form_data = {"end_time": timezone.now(), "emotional_status": status}
            form = EndFastForm(data=form_data, instance=self.fast)

            assert form.is_valid(), f"Form should be valid for status: {status}"

    def test_end_fast_form_comments_max_length(self):
        """Test form with very long comments."""
        long_comment = "A" * 1001  # Exceeds max_length of 1000

        form_data = {
            "end_time": timezone.now(),
            "emotional_status": "satisfied",
            "comments": long_comment,
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        assert not form.is_valid()
        assert "comments" in form.errors

    def test_end_fast_form_comments_optional(self):
        """Test that comments field is optional."""
        form_data = {"end_time": timezone.now(), "emotional_status": "satisfied"}
        form = EndFastForm(data=form_data, instance=self.fast)

        assert form.is_valid()

    def test_end_fast_form_save(self):
        """Test form save method."""
        end_time = timezone.now()
        form_data = {
            "end_time": end_time,
            "emotional_status": "energized",
            "comments": "Great fast experience!",
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        assert form.is_valid()

        saved_fast = form.save()

        assert saved_fast.pk == self.fast.pk
        assert saved_fast.end_time == end_time
        assert saved_fast.emotional_status == "energized"
        assert saved_fast.comments == "Great fast experience!"

    def test_end_fast_form_widget_attributes(self):
        """Test form widget attributes for proper rendering."""
        form = EndFastForm(instance=self.fast)

        # Check end_time widget
        end_time_widget = form.fields["end_time"].widget
        assert end_time_widget.input_type == "datetime-local"
        assert "class" in end_time_widget.attrs

        # Check emotional_status widget
        emotional_status_widget = form.fields["emotional_status"].widget
        assert "class" in emotional_status_widget.attrs

        # Check comments widget
        comments_widget = form.fields["comments"].widget
        assert "class" in comments_widget.attrs
        assert "rows" in comments_widget.attrs

    def test_end_fast_form_help_texts(self):
        """Test form help texts."""
        form = EndFastForm(instance=self.fast)

        end_time_help = form.fields["end_time"].help_text
        assert "When the fast ended" in end_time_help

        emotional_status_help = form.fields["emotional_status"].help_text
        assert "emotional state when ending fast" in emotional_status_help

        comments_help = form.fields["comments"].help_text
        assert "User's reflection on the fast" in comments_help

    def test_end_fast_form_labels(self):
        """Test form field labels."""
        form = EndFastForm(instance=self.fast)

        assert form.fields["end_time"].label == "End Time"
        assert form.fields["emotional_status"].label == "How did you feel?"
        assert form.fields["comments"].label == "Comments"

    def test_end_fast_form_field_order(self):
        """Test form field order."""
        form = EndFastForm(instance=self.fast)

        field_names = list(form.fields.keys())
        expected_order = ["end_time", "emotional_status", "comments"]

        assert field_names == expected_order

    def test_end_fast_form_very_short_fast(self):
        """Test ending a fast that's very short (less than 30 minutes)."""
        short_fast = FastFactory.create(
            start_time=timezone.now() - timedelta(minutes=15),
        )

        form_data = {"end_time": timezone.now(), "emotional_status": "satisfied"}
        form = EndFastForm(data=form_data, instance=short_fast)

        assert not form.is_valid()
        assert "end_time" in form.errors
        assert "duration must be at least" in form.errors["end_time"][0]

    def test_end_fast_form_exact_30_minutes(self):
        """Test ending a fast that's exactly 30 minutes (boundary condition)."""
        exact_fast = FastFactory.create(
            start_time=timezone.now() - timedelta(minutes=30),
        )

        form_data = {"end_time": timezone.now(), "emotional_status": "satisfied"}
        form = EndFastForm(data=form_data, instance=exact_fast)

        assert form.is_valid()

    def test_end_fast_form_very_long_fast(self):
        """Test ending a very long fast (more than 7 days)."""
        long_fast = FastFactory.create(start_time=timezone.now() - timedelta(days=8))

        form_data = {"end_time": timezone.now(), "emotional_status": "satisfied"}
        form = EndFastForm(data=form_data, instance=long_fast)

        # This should be valid - no upper limit on fast duration
        assert not form.is_valid()
        assert "Fast duration cannot exceed" in form.errors["end_time"][0]

    def test_end_fast_form_clean_method_called(self):
        """Test that the clean method is properly called during validation."""
        # Test with invalid data to ensure clean method catches it
        form_data = {
            "end_time": self.fast.start_time - timedelta(hours=1),  # Before start
            "emotional_status": "satisfied",
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        # This should call clean() and detect the validation error
        assert not form.is_valid()

    def test_end_fast_form_with_already_ended_fast(self):
        """Test form with a fast that's already been ended."""
        ended_fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now() - timedelta(hours=2),
            emotional_status="satisfied",
        )

        form_data = {
            "end_time": timezone.now(),
            "emotional_status": "energized",
            "comments": "Updating ended fast",
        }
        form = EndFastForm(data=form_data, instance=ended_fast)

        # This should be valid - allows editing already ended fasts
        assert form.is_valid()

    def test_end_fast_form_preserve_start_time(self):
        """Test that form doesn't change the start time."""
        original_start = self.fast.start_time

        form_data = {"end_time": timezone.now(), "emotional_status": "satisfied"}
        form = EndFastForm(data=form_data, instance=self.fast)

        assert form.is_valid()
        saved_fast = form.save()

        # Start time should remain unchanged
        assert saved_fast.start_time == original_start

    def test_end_fast_form_preserve_user(self):
        """Test that form doesn't change the user."""
        original_user = self.fast.user

        form_data = {"end_time": timezone.now(), "emotional_status": "satisfied"}
        form = EndFastForm(data=form_data, instance=self.fast)

        assert form.is_valid()
        saved_fast = form.save()

        # User should remain unchanged
        assert saved_fast.user == original_user


class FormIntegrationTest(TestCase):
    """Integration tests for form functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    def test_complete_fast_workflow(self):
        """Test complete workflow from start to end form."""
        # Start a fast
        start_form_data = {"start_time": timezone.now() - timedelta(hours=16)}
        start_form = StartFastForm(data=start_form_data, user=self.user)

        assert start_form.is_valid()
        fast = start_form.save()

        # End the fast
        end_form_data = {
            "end_time": timezone.now(),
            "emotional_status": "energized",
            "comments": "Great experience!",
        }
        end_form = EndFastForm(data=end_form_data, instance=fast)

        assert end_form.is_valid()
        ended_fast = end_form.save()

        # Verify complete fast
        assert ended_fast.end_time is not None
        assert ended_fast.emotional_status == "energized"
        assert ended_fast.comments == "Great experience!"
        assert ended_fast.duration.total_seconds() > 0

    def test_form_validation_consistency(self):
        """Test that form validation is consistent with model validation."""
        # Create a fast with invalid data that should fail at both levels
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=1),
        )

        # Try to end with invalid end time
        invalid_end_data = {
            "end_time": fast.start_time - timedelta(minutes=30),  # Before start
            "emotional_status": "satisfied",
        }

        # Form validation should catch this
        form = EndFastForm(data=invalid_end_data, instance=fast)
        assert not form.is_valid()

        # If we somehow bypass form validation, model validation should also catch it
        fast.end_time = invalid_end_data["end_time"]
        fast.emotional_status = invalid_end_data["emotional_status"]

        with pytest.raises(ValidationError):
            fast.full_clean()
