from django.conf import settings
from django.db import models
from django.dispatch import receiver

from yolapi.pypi.models import Distribution
import yolapi.eggbuilder.tasks


if getattr(settings, 'PYPI_EGG_PYVERSIONS'):
    @receiver(models.signals.post_save)
    def _distribution_save(sender, **kwargs):
        if sender == Distribution and not kwargs['raw'] and kwargs['created']:
            distribution = kwargs['instance']
            if distribution.filetype == 'sdist':
                for pyversion in getattr(settings, 'PYPI_EGG_PYVERSIONS'):
                    yolapi.eggbuilder.tasks.build_egg.delay(
                            distribution.release.package.name,
                            distribution.release.version,
                            pyversion)
