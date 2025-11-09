"""
Comprehensive form tests for the fasting app.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from healthy_herron.fasting.forms import StartFastForm, EndFastForm
from healthy_herron.fasting.models import Fast
from healthy_herron.fasting.tests.factories import UserFactory, FastFactory


class FastFormTest(TestCase):
    """Test the FastForm for starting new fasts."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    def test_fast_form_valid_data(self):
        """Test form with valid data."""
        form_data = {
            'start_time': timezone.now() - timedelta(hours=1)
        }
        form = StartFastForm(data=form_data, user=self.user)

        self.assertTrue(form.is_valid())

    def test_fast_form_future_start_time(self):
        """Test form with future start time."""
        form_data = {
            'start_time': timezone.now() + timedelta(hours=1)
        }
        form = StartFastForm(data=form_data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('start_time', form.errors)
        self.assertIn('cannot be in the future', str(form.errors['start_time']))

    def test_fast_form_very_old_start_time(self):
        """Test form with very old start time (more than 7 days ago)."""
        form_data = {
            'start_time': timezone.now() - timedelta(days=8)
        }
        form = StartFastForm(data=form_data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('start_time', form.errors)
        self.assertIn('cannot be more than 7 days ago', str(form.errors['start_time']))

    def test_fast_form_with_existing_active_fast(self):
        """Test form when user already has an active fast."""
        # Create existing active fast
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=5)
        )

        form_data = {
            'start_time': timezone.now() - timedelta(hours=1)
        }
        form = StartFastForm(data=form_data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('already have an active fast', str(form.errors['__all__']))

    def test_fast_form_missing_start_time(self):
        """Test form with missing start time."""
        form_data = {}
        form = StartFastForm(data=form_data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('start_time', form.errors)

    def test_fast_form_invalid_start_time_format(self):
        """Test form with invalid start time format."""
        form_data = {
            'start_time': 'invalid-date'
        }
        form = StartFastForm(data=form_data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('start_time', form.errors)

    def test_fast_form_save(self):
        """Test form save method."""
        form_data = {
            'start_time': timezone.now() - timedelta(hours=2)
        }
        form = StartFastForm(data=form_data, user=self.user)

        self.assertTrue(form.is_valid())

        fast = form.save()

        self.assertIsInstance(fast, Fast)
        self.assertEqual(fast.user, self.user)
        self.assertEqual(fast.start_time, form_data['start_time'])
        self.assertIsNone(fast.end_time)
        self.assertIsNone(fast.emotional_status)

    def test_fast_form_widget_attributes(self):
        """Test form widget attributes for proper rendering."""
        form = StartFastForm(user=self.user)

        start_time_widget = form.fields['start_time'].widget
        self.assertEqual(start_time_widget.input_type, 'datetime-local')
        self.assertIn('class', start_time_widget.attrs)

    def test_fast_form_help_text(self):
        """Test form help text."""
        form = StartFastForm(user=self.user)

        help_text = form.fields['start_time'].help_text
        self.assertIn('When did you start', help_text)

    def test_fast_form_label(self):
        """Test form field labels."""
        form = StartFastForm(user=self.user)

        self.assertEqual(form.fields['start_time'].label, 'Start Time')


class EndFastFormTest(TestCase):
    """Test the EndFastForm for ending active fasts."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16)
        )

    def test_end_fast_form_valid_data(self):
        """Test form with valid data."""
        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'energized',
            'comments': 'Felt great during this fast!'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertTrue(form.is_valid())

    def test_end_fast_form_minimal_valid_data(self):
        """Test form with minimal required data."""
        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertTrue(form.is_valid())

    def test_end_fast_form_missing_emotional_status(self):
        """Test form with missing emotional status."""
        form_data = {
            'end_time': timezone.now(),
            'comments': 'Test comment'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertFalse(form.is_valid())
        self.assertIn('emotional_status', form.errors)

    def test_end_fast_form_missing_end_time(self):
        """Test form with missing end time."""
        form_data = {
            'emotional_status': 'satisfied',
            'comments': 'Test comment'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)

    def test_end_fast_form_end_time_before_start_time(self):
        """Test form with end time before start time."""
        form_data = {
            'end_time': self.fast.start_time - timedelta(hours=1),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)
        self.assertIn('End time must be after the start time.', str(form.errors['end_time']))


    def test_end_fast_form_invalid_emotional_status(self):
        """Test form with invalid emotional status."""
        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'invalid_status'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertFalse(form.is_valid())
        self.assertIn('emotional_status', form.errors)

    def test_end_fast_form_valid_emotional_statuses(self):
        """Test form with all valid emotional statuses."""
        valid_statuses = ['hungry', 'satisfied', 'energized', 'weak', 'focused']

        for status in valid_statuses:
            form_data = {
                'end_time': timezone.now(),
                'emotional_status': status
            }
            form = EndFastForm(data=form_data, instance=self.fast)

            self.assertTrue(form.is_valid(), f"Form should be valid for status: {status}")

    def test_end_fast_form_comments_max_length(self):
        """Test form with very long comments."""
        long_comment = 'A' * 1001  # Exceeds max_length of 1000

        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied',
            'comments': long_comment
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertFalse(form.is_valid())
        self.assertIn('comments', form.errors)

    def test_end_fast_form_comments_optional(self):
        """Test that comments field is optional."""
        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertTrue(form.is_valid())

    def test_end_fast_form_save(self):
        """Test form save method."""
        end_time = timezone.now()
        form_data = {
            'end_time': end_time,
            'emotional_status': 'energized',
            'comments': 'Great fast experience!'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertTrue(form.is_valid())

        saved_fast = form.save()

        self.assertEqual(saved_fast.pk, self.fast.pk)
        self.assertEqual(saved_fast.end_time, end_time)
        self.assertEqual(saved_fast.emotional_status, 'energized')
        self.assertEqual(saved_fast.comments, 'Great fast experience!')

    def test_end_fast_form_widget_attributes(self):
        """Test form widget attributes for proper rendering."""
        form = EndFastForm(instance=self.fast)

        # Check end_time widget
        end_time_widget = form.fields['end_time'].widget
        self.assertEqual(end_time_widget.input_type, 'datetime-local')
        self.assertIn('class', end_time_widget.attrs)

        # Check emotional_status widget
        emotional_status_widget = form.fields['emotional_status'].widget
        self.assertIn('class', emotional_status_widget.attrs)

        # Check comments widget
        comments_widget = form.fields['comments'].widget
        self.assertIn('class', comments_widget.attrs)
        self.assertIn('rows', comments_widget.attrs)

    def test_end_fast_form_help_texts(self):
        """Test form help texts."""
        form = EndFastForm(instance=self.fast)

        end_time_help = form.fields['end_time'].help_text
        self.assertIn('When the fast ended', end_time_help)

        emotional_status_help = form.fields['emotional_status'].help_text
        self.assertIn('emotional state when ending fast', emotional_status_help)

        comments_help = form.fields['comments'].help_text
        self.assertIn("User's reflection on the fast", comments_help)

    def test_end_fast_form_labels(self):
        """Test form field labels."""
        form = EndFastForm(instance=self.fast)

        self.assertEqual(form.fields['end_time'].label, 'End Time')
        self.assertEqual(form.fields['emotional_status'].label, 'How did you feel?')
        self.assertEqual(form.fields['comments'].label, 'Comments')

    def test_end_fast_form_field_order(self):
        """Test form field order."""
        form = EndFastForm(instance=self.fast)

        field_names = list(form.fields.keys())
        expected_order = ['end_time', 'emotional_status', 'comments']

        self.assertEqual(field_names, expected_order)

    def test_end_fast_form_very_short_fast(self):
        """Test ending a fast that's very short (less than 30 minutes)."""
        short_fast = FastFactory.create(
            start_time=timezone.now() - timedelta(minutes=15)
        )

        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=short_fast)

        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('must be at least 30 minutes', str(form.errors['__all__']))

    def test_end_fast_form_exact_30_minutes(self):
        """Test ending a fast that's exactly 30 minutes (boundary condition)."""
        exact_fast = FastFactory.create(
            start_time=timezone.now() - timedelta(minutes=30)
        )

        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=exact_fast)

        self.assertTrue(form.is_valid())

    def test_end_fast_form_very_long_fast(self):
        """Test ending a very long fast (more than 7 days)."""
        long_fast = FastFactory.create(
            start_time=timezone.now() - timedelta(days=8)
        )

        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=long_fast)

        # This should be valid - no upper limit on fast duration
        self.assertTrue(form.is_valid())

    def test_end_fast_form_clean_method_called(self):
        """Test that the clean method is properly called during validation."""
        # Test with invalid data to ensure clean method catches it
        form_data = {
            'end_time': self.fast.start_time - timedelta(hours=1),  # Before start
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        # This should call clean() and detect the validation error
        self.assertFalse(form.is_valid())

    def test_end_fast_form_with_already_ended_fast(self):
        """Test form with a fast that's already been ended."""
        ended_fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now() - timedelta(hours=2),
            emotional_status='satisfied'
        )

        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'energized',
            'comments': 'Updating ended fast'
        }
        form = EndFastForm(data=form_data, instance=ended_fast)

        # This should be valid - allows editing already ended fasts
        self.assertTrue(form.is_valid())

    def test_end_fast_form_preserve_start_time(self):
        """Test that form doesn't change the start time."""
        original_start = self.fast.start_time

        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertTrue(form.is_valid())
        saved_fast = form.save()

        # Start time should remain unchanged
        self.assertEqual(saved_fast.start_time, original_start)

    def test_end_fast_form_preserve_user(self):
        """Test that form doesn't change the user."""
        original_user = self.fast.user

        form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'satisfied'
        }
        form = EndFastForm(data=form_data, instance=self.fast)

        self.assertTrue(form.is_valid())
        saved_fast = form.save()

        # User should remain unchanged
        self.assertEqual(saved_fast.user, original_user)


class FormIntegrationTest(TestCase):
    """Integration tests for form functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    def test_complete_fast_workflow(self):
        """Test complete workflow from start to end form."""
        # Start a fast
        start_form_data = {
            'start_time': timezone.now() - timedelta(hours=16)
        }
        start_form = StartFastForm(data=start_form_data, user=self.user)

        self.assertTrue(start_form.is_valid())
        fast = start_form.save()

        # End the fast
        end_form_data = {
            'end_time': timezone.now(),
            'emotional_status': 'energized',
            'comments': 'Great experience!'
        }
        end_form = EndFastForm(data=end_form_data, instance=fast)

        self.assertTrue(end_form.is_valid())
        ended_fast = end_form.save()

        # Verify complete fast
        self.assertIsNotNone(ended_fast.end_time)
        self.assertEqual(ended_fast.emotional_status, 'energized')
        self.assertEqual(ended_fast.comments, 'Great experience!')
        self.assertTrue(ended_fast.duration.total_seconds() > 0)

    def test_form_validation_consistency(self):
        """Test that form validation is consistent with model validation."""
        # Create a fast with invalid data that should fail at both levels
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=1)
        )

        # Try to end with invalid end time
        invalid_end_data = {
            'end_time': fast.start_time - timedelta(minutes=30),  # Before start
            'emotional_status': 'satisfied'
        }

        # Form validation should catch this
        form = EndFastForm(data=invalid_end_data, instance=fast)
        self.assertFalse(form.is_valid())

        # If we somehow bypass form validation, model validation should also catch it
        fast.end_time = invalid_end_data['end_time']
        fast.emotional_status = invalid_end_data['emotional_status']

        with self.assertRaises(ValidationError):
            fast.full_clean()
