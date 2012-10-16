from django.conf import settings
from django.dispatch import receiver
from django.db import models

from yolapi.pypi.models import Distribution
import yolapi.sync.tasks


if getattr(settings, 'PYPI_SYNC_BUCKET'):
    @receiver(models.signals.post_save)
    def _distribution_save(sender, **kwargs):
        if sender == Distribution and not kwargs['raw'] and kwargs['created']:
            yolapi.sync.tasks.push.delay(kwargs['instance'].id)
