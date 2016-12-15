import urllib

from django.core.management.base import BaseCommand

from pypi.models import Distribution
from sync.tasks import _bucket


class Command(BaseCommand):
    help = 'Set uploaded timestamps in S3'

    def handle(self, *args, **options):
        bucket = _bucket()
        for distribution in Distribution.objects.iterator():
            print distribution
            key = bucket.get_key(u'dists/%s' % distribution.filename)
            if not key.get_metadata('uploaded'):
                uploaded = urllib.quote(distribution.created.isoformat())
                key.set_metadata('uploaded', uploaded)
                key.copy(bucket.name, key.name, key.metadata, preserve_acl=True)
