import os
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from pypi.models import Distribution


class Command(BaseCommand):
    help = 'List orphaned distributions on the filesystem'
    option_list = BaseCommand.option_list + (
        make_option('--delete',
                    action='store_true',
                    dest='delete',
                    default=False,
                    help='Delete orphaned files instead of simply listing'),
    )

    def handle(self, *args, **options):
        directory = os.path.join(settings.MEDIA_ROOT,
                                 getattr(settings, 'PYPI_DISTS', 'dists'))
        on_disk = set(os.listdir(directory))
        owned = set()
        for distribution in Distribution.objects.iterator():
            owned.add(distribution.filename)

        orphans = on_disk.difference(owned)

        for filename in sorted(orphans):
            print filename
            if options['delete']:
                os.unlink(os.path.join(directory, filename))
