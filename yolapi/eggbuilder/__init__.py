from django.conf import settings
from django.db import models
from django.dispatch import receiver

from pypi.models import Distribution
import eggbuilder.tasks


if getattr(settings, 'PYPI_EGG_PYVERSIONS'):
    @receiver(models.signals.post_save, sender=Distribution)
    def _distribution_save(**kwargs):
        if kwargs['created'] and not kwargs['raw']:
            distribution = kwargs['instance']
            if distribution.filetype == 'sdist':
                for pyversion in getattr(settings, 'PYPI_EGG_PYVERSIONS'):
                    eggbuilder.tasks.build_egg.delay(
                            distribution.release.package.name,
                            distribution.release.version,
                            pyversion)
