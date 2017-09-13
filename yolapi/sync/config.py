from django.apps import AppConfig
from django.conf import settings
from django.db import models
from django.dispatch import receiver


class SyncConfig(AppConfig):
    name = 'sync'

    def ready(self):
        from pypi.models import Distribution
        from sync.tasks import push

        if getattr(settings, 'PYPI_SYNC_BUCKET'):
            @receiver(models.signals.post_save, sender=Distribution)
            def _distribution_save(**kwargs):
                if kwargs['created'] and not kwargs['raw']:
                    if not kwargs['instance'].sync_imported:
                        push.delay(kwargs['instance'].id)
