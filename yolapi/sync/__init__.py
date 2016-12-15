from django.conf import settings
from django.dispatch import receiver
from django.db import models

from pypi.models import Distribution
import sync.tasks


if getattr(settings, 'PYPI_SYNC_BUCKET'):
    @receiver(models.signals.post_save, sender=Distribution)
    def _distribution_save(**kwargs):
        if kwargs['created'] and not kwargs['raw']:
            if not kwargs['instance'].sync_imported:
                sync.tasks.push.delay(kwargs['instance'].id)
