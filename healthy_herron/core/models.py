from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

User = get_user_model()


class AuditableModel(models.Model):
    """Abstract model to keep track of who created or modified the model.

    Attributes:
        created_by (ForeignKey): Reference to the user who created the instance.
        modified_by (ForeignKey): Reference to the user who last modified the instance.
    """

    created_by = models.ForeignKey(
        User, related_name="%(class)s_created", on_delete=models.PROTECT, null=True, blank=True
    )
    modified_by = models.ForeignKey(
        User, related_name="%(class)s_modified", on_delete=models.PROTECT, null=True, blank=True
    )

    class Meta:
        abstract = True
