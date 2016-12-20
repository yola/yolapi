from django.conf import settings
from django.db import models
from django.dispatch import receiver

from pypi.models import Distribution
import wheelbuilder.tasks


if getattr(settings, 'PYPI_WHEEL_TAGS'):
    @receiver(models.signals.post_save, sender=Distribution)
    def _distribution_save(**kwargs):
        if kwargs['created'] and not kwargs['raw']:
            distribution = kwargs['instance']
            if distribution.filetype == 'sdist':
                for tag in getattr(settings, 'PYPI_WHEEL_TAGS'):
                    wheelbuilder.tasks.build_wheel.delay(
                            distribution.release.package.name,
                            distribution.release.version, tag)
