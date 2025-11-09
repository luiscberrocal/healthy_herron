"""
Comprehensive view tests for the fasting app.
"""
import unittest

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock
from django.contrib.messages import get_messages

from healthy_herron.fasting.models import Fast
from healthy_herron.fasting.tests.factories import UserFactory, FastFactory

User = get_user_model()


class DashboardViewTest(TestCase):
    """Test the dashboard view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.client = Client()
        self.url = reverse('fasting:dashboard')

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_dashboard_with_no_fasts(self):
        """Test dashboard when user has no fasts."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, " You don't currently have an active fast")

    def test_dashboard_with_active_fast(self):
        """Test dashboard when user has an active fast."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=5)
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Fast')
        self.assertContains(response, 'End Fast')

    def test_dashboard_with_recent_fasts(self):
        """Test dashboard shows recent completed fasts."""
        # Create some completed fasts
        for i in range(3):
            Fast.objects.create(
                user=self.user,
                start_time=timezone.now() - timedelta(days=i+1, hours=16),
                end_time=timezone.now() - timedelta(days=i+1),
                emotional_status='satisfied'
            )

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent Fasts')


class StartFastViewTest(TestCase):
    """Test the start fast view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.client = Client()
        self.url = reverse('fasting:start_fast')

    def test_start_fast_requires_login(self):
        """Test that start fast requires authentication."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_start_fast_get(self):
        """Test GET request to start fast view."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Start New Fast')
        self.assertContains(response, 'start_time')

    @unittest.skip("Need to fix this")
    def test_start_fast_post_success(self):
        """Test successful fast creation."""
        self.client.force_login(self.user)

        post_data = {
            'start_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
        }

        response = self.client.post(self.url, post_data)

        # Should redirect to dashboard
        self.assertRedirects(response, reverse('fasting:dashboard'))

        # Fast should be created
        self.assertEqual(Fast.objects.filter(user=self.user).count(), 1)

        # Success message should be displayed
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Fast started successfully' in str(m) for m in messages))

    def test_start_fast_with_existing_active_fast(self):
        """Test starting fast when user already has active fast."""
        # Create existing active fast
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=2)
        )

        self.client.force_login(self.user)

        post_data = {
            'start_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
        }

        response = self.client.post(self.url, post_data)

        # Should show form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already have an active fast')

        # Should still only have one fast
        self.assertEqual(Fast.objects.filter(user=self.user).count(), 1)


class EndFastViewTest(TestCase):
    """Test the end fast view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.client = Client()
        self.url = reverse('fasting:end_fast')

    def test_end_fast_requires_login(self):
        """Test that end fast requires authentication."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_end_fast_without_active_fast(self):
        """Test end fast when user has no active fast."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_end_fast_get_with_active_fast(self):
        """Test GET request to end fast with active fast."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=12)
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'End Your Fast')
        self.assertContains(response, 'emotional_status')

    @unittest.skip("Need to fix this")
    def test_end_fast_post_success(self):
        """Test successful fast completion."""
        url = reverse('fasting:end_fast')
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16)
        )

        self.client.force_login(self.user)

        post_data = {
            'end_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'emotional_status': 'energized',
            'comments': 'Felt great!'
        }

        response = self.client.post(url, post_data)

        # Should redirect to dashboard
        self.assertRedirects(response, reverse('fasting:dashboard'))

        # Fast should be completed
        fast.refresh_from_db()
        self.assertIsNotNone(fast.end_time)
        self.assertEqual(fast.emotional_status, 'energized')
        self.assertEqual(fast.comments, 'Felt great!')

        # Success message should be displayed
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Fast completed successfully' in str(m) for m in messages))

    def test_end_fast_validation_error(self):
        """Test end fast with validation errors."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16)
        )

        self.client.force_login(self.user)

        # Missing required emotional_status
        post_data = {
            'end_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'comments': 'Test comment'
        }

        response = self.client.post(self.url, post_data)

        # Should show form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error')

        # Fast should still be active
        fast.refresh_from_db()
        self.assertIsNone(fast.end_time)


class FastListViewTest(TestCase):
    """Test the fast list view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.client = Client()
        self.url = reverse('fasting:fast_list')

    def test_fast_list_requires_login(self):
        """Test that fast list requires authentication."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_fast_list_shows_only_user_fasts(self):
        """Test that fast list shows only the user's fasts."""
        # Create fasts for both users
        user_fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(hours=8),
            emotional_status='satisfied'
        )
        other_user_fast = Fast.objects.create(
            user=self.other_user,
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1, hours=8),
            emotional_status='energized'
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Satisfied")
        self.assertNotContains(response, "Energized")

    def test_fast_list_pagination(self):
        """Test pagination in fast list."""
        # Create more than 20 fasts to test pagination
        for i in range(25):
            Fast.objects.create(
                user=self.user,
                start_time=timezone.now() - timedelta(days=i+1, hours=16),
                end_time=timezone.now() - timedelta(days=i+1),
                emotional_status='satisfied'
            )

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Page')  # Pagination controls

        # Should show 20 fasts per page
        self.assertEqual(len(response.context['fasts']), 20)

    def test_fast_list_statistics(self):
        """Test statistics display in fast list."""
        # Create various types of fasts
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=5)  # Active
        )
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(days=1, hours=16),
            end_time=timezone.now() - timedelta(days=1),
            emotional_status='satisfied'  # Completed
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_fasts'], 2)
        self.assertEqual(response.context['completed_fasts'], 1)
        self.assertEqual(response.context['active_fasts'], 1)


class FastDetailViewTest(TestCase):
    """Test the fast detail view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.client = Client()

    def test_fast_detail_requires_login(self):
        """Test that fast detail requires authentication."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now()
        )
        url = reverse('fasting:fast_detail', kwargs={'pk': fast.pk})

        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_fast_detail_user_ownership(self):
        """Test that users can only view their own fasts."""
        other_user_fast = Fast.objects.create(
            user=self.other_user,
            start_time=timezone.now()
        )
        url = reverse('fasting:fast_detail', kwargs={'pk': other_user_fast.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_fast_detail_success(self):
        """Test successful fast detail view."""
        fast = FastFactory.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status='energized',
            comments='Great fast!'
        )
        url = reverse('fasting:fast_detail', kwargs={'pk': fast.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fast Details')
        self.assertContains(response, "Energized")
        self.assertContains(response, fast.comments)

    def test_fast_detail_navigation(self):
        """Test navigation between fasts in detail view."""
        # Create multiple fasts
        fast1 = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1, hours=8),
            emotional_status='satisfied'
        )
        fast2 = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(hours=8),
            emotional_status='energized'
        )

        url = reverse('fasting:fast_detail', kwargs={'pk': fast1.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Should show navigation to newer fast
        self.assertContains(response, 'Next Fast')


class FastUpdateViewTest(TestCase):
    """Test the fast update view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.client = Client()

    def test_fast_update_requires_login(self):
        """Test that fast update requires authentication."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now()
        )
        url = reverse('fasting:fast_update', kwargs={'pk': fast.pk})

        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_fast_update_user_ownership(self):
        """Test that users can only update their own fasts."""
        other_user_fast = Fast.objects.create(
            user=self.other_user,
            start_time=timezone.now()
        )
        url = reverse('fasting:fast_update', kwargs={'pk': other_user_fast.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_fast_update_get(self):
        """Test GET request to fast update."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status='satisfied',
            comments='Test comment'
        )
        url = reverse('fasting:fast_update', kwargs={'pk': fast.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Fast')
        self.assertContains(response, fast.comments)

    def test_fast_update_post_success(self):
        """Test successful fast update."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status='satisfied',
            comments='Original comment'
        )
        url = reverse('fasting:fast_update', kwargs={'pk': fast.pk})

        self.client.force_login(self.user)

        post_data = {
            'start_time': fast.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': fast.end_time.strftime('%Y-%m-%dT%H:%M'),
            'emotional_status': 'energized',
            'comments': 'Updated comment'
        }

        response = self.client.post(url, post_data)

        # Should redirect to detail view
        self.assertRedirects(response, reverse('fasting:fast_detail', kwargs={'pk': fast.pk}))

        # Fast should be updated
        fast.refresh_from_db()
        self.assertEqual(fast.emotional_status, 'energized')
        self.assertEqual(fast.comments, 'Updated comment')


class FastDeleteViewTest(TestCase):
    """Test the fast delete view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.client = Client()

    def test_fast_delete_requires_login(self):
        """Test that fast delete requires authentication."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now()
        )
        url = reverse('fasting:fast_delete', kwargs={'pk': fast.pk})

        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_fast_delete_user_ownership(self):
        """Test that users can only delete their own fasts."""
        other_user_fast = Fast.objects.create(
            user=self.other_user,
            start_time=timezone.now()
        )
        url = reverse('fasting:fast_delete', kwargs={'pk': other_user_fast.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_fast_delete_get(self):
        """Test GET request to fast delete (confirmation page)."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status='satisfied'
        )
        url = reverse('fasting:fast_delete', kwargs={'pk': fast.pk})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Fast')
        self.assertContains(response, 'Are you sure')

    def test_fast_delete_post_success(self):
        """Test successful fast deletion."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=16),
            end_time=timezone.now(),
            emotional_status='satisfied'
        )
        url = reverse('fasting:fast_delete', kwargs={'pk': fast.pk})

        self.client.force_login(self.user)
        response = self.client.post(url)

        # Should redirect to fast list
        self.assertRedirects(response, reverse('fasting:fast_list'))

        # Fast should be deleted
        self.assertFalse(Fast.objects.filter(pk=fast.pk).exists())

@unittest.skip("Need to fix this")
class ExportDataViewTest(TestCase):
    """Test the export data view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.client = Client()

    def test_export_requires_login(self):
        """Test that export requires authentication."""
        url = reverse('fasting:export_data', kwargs={'format': 'csv'})
        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_export_csv(self):
        """Test CSV export functionality."""
        # Create test data
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(days=1, hours=16),
            end_time=timezone.now() - timedelta(days=1),
            emotional_status='satisfied',
            comments='Test fast'
        )

        url = reverse('fasting:export_data', kwargs={'format': 'csv'})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Start Time', content)
        self.assertIn('satisfied', content)

    def test_export_json(self):
        """Test JSON export functionality."""
        # Create test data
        Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(days=1, hours=16),
            end_time=timezone.now() - timedelta(days=1),
            emotional_status='energized',
            comments='JSON test'
        )

        url = reverse('fasting:export_data', kwargs={'format': 'json'})

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_invalid_format(self):
        """Test export with invalid format."""
        url = reverse('fasting:export_data', kwargs={'format': 'xml'})

        self.client.force_login(self.user)
        response = self.client.get(url)

        # Should redirect to fast list with error message
        self.assertRedirects(response, reverse('fasting:fast_list'))


class TimerUpdateViewTest(TestCase):
    """Test the HTMX timer update view."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.client = Client()
        self.url = reverse('fasting:timer_update')

    @unittest.skip("Need to fix this")
    def test_timer_update_unauthenticated(self):
        """Test timer update for unauthenticated user."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'active_fast')  # Template variable

    def test_timer_update_with_active_fast(self):
        """Test timer update with active fast."""
        fast = Fast.objects.create(
            user=self.user,
            start_time=timezone.now() - timedelta(hours=5)
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        # Should return timer fragment with elapsed time
        self.assertContains(response, 'h')  # Hours indicator

    def test_timer_update_no_active_fast(self):
        """Test timer update when user has no active fast."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        # Should return empty timer fragment
