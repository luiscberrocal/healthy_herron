from django.conf import settings
from django.db import models


class AuditableModel(models.Model):
    """Abstract model to keep track of who created or modified the model.

    Attributes:
        created_by (ForeignKey): Reference to the user who created the instance.
        modified_by (ForeignKey): Reference to the user who last modified the instance.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_created",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_modified",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract model that adds timestamp fields.

    Attributes:
        created_at (DateTimeField): When the instance was created.
        updated_at (DateTimeField): When the instance was last updated.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
