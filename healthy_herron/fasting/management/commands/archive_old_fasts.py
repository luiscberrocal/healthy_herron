"""
Django management command to archive old fasting records.

This command archives Fast records that are older than 2 years by moving them
to an archived state or separate table to maintain database performance.
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from healthy_herron.fasting.models import Fast

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Archive fasting records older than 2 years"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be archived without actually doing it",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=730,  # 2 years
            help="Archive records older than this many days (default: 730)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Process records in batches of this size (default: 1000)",
        )

    def handle(self, *args, **options):
        """Execute the archival process."""
        dry_run = options["dry_run"]
        days_threshold = options["days"]
        batch_size = options["batch_size"]

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days_threshold)

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting archival process for fasts older than {cutoff_date.date()}",
            ),
        )

        # Find old fasts that are completed (have end_time)
        old_fasts = Fast.objects.filter(
            end_time__lt=cutoff_date,
            end_time__isnull=False,  # Only archive completed fasts
        ).order_by("start_time")

        total_count = old_fasts.count()

        if total_count == 0:
            self.stdout.write(self.style.WARNING("No fasts found for archival."))
            return

        self.stdout.write(
            self.style.WARNING(f"Found {total_count} fasts eligible for archival"),
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE: No changes will be made"),
            )

            # Show sample of what would be archived
            sample_fasts = old_fasts[:10]
            for fast in sample_fasts:
                self.stdout.write(
                    f"  - Fast ID {fast.id}: {fast.start_time.date()} to {fast.end_time.date() if fast.end_time else 'ongoing'} (User: {fast.user.email})",
                )

            if total_count > 10:
                self.stdout.write(f"  ... and {total_count - 10} more")

            return

        # Confirm before proceeding
        confirm = input(
            f"Are you sure you want to archive {total_count} fast records? (yes/no): ",
        )
        if confirm.lower() != "yes":
            self.stdout.write(self.style.ERROR("Archival cancelled by user."))
            return

        # Process in batches
        archived_count = 0

        try:
            with transaction.atomic():
                for i in range(0, total_count, batch_size):
                    batch = old_fasts[i : i + batch_size]

                    for fast in batch:
                        # For now, we'll add an 'archived' flag to the model
                        # In a full implementation, you might move to a separate table
                        fast.is_archived = True
                        fast.archived_at = timezone.now()
                        fast.save(update_fields=["is_archived", "archived_at"])
                        archived_count += 1

                    self.stdout.write(
                        f"Archived batch {i // batch_size + 1}: {min(i + batch_size, total_count)}/{total_count} records",
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully archived {archived_count} fast records",
                    ),
                )

        except Exception as e:
            logger.exception(f"Error during archival: {e}")
            msg = f"Archival failed: {e}"
            raise CommandError(msg)

    def _create_archived_fast_table(self):
        """
        Create archived fast table if it doesn't exist.
        This would be used in a full implementation to move old records
        to a separate table for better performance.
        """
        # This would use raw SQL or migrations to create an archived table
        # with the same structure as Fast but for archived records
