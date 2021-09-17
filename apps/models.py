from uuid import uuid4

from django.db import models


class BaseAbstractModel(models.Model):
    """Specifies fields required by models implementing this class"""

    uuid = models.UUIDField(unique=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
