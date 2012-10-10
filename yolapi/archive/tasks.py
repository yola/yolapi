import base64
import logging

from boto.s3.connection import S3Connection
from celery import task
from django.conf import settings

from pypi.models import Distribution

log = logging.getLogger(__name__)


@task(ignore_result=True)
def update_archive():
    """Spawn jobs to archive anything that isn't present in S3"""
    bucket = _archive_bucket()
    for distribution in Distribution.objects.all():
        key = bucket.get_key(distribution.filename)
        if key is None:
            md5 = None
        else:
            md5 = key.get_metadata('md5_digest')
        if md5 != distribution.md5_digest:
            archive_distribution.delay(distribution.id)


@task(ignore_result=True)
def archive_distribution(id):
    """Archive a Distribution to S3, and update its metadata in S3"""
    distribution = Distribution.objects.get(id=id)
    release = distribution.release
    log.info("Archiving %s" % distribution.filename)

    bucket = _archive_bucket()
    key = bucket.new_key(distribution.filename)

    key.set_metadata('md5_digest', distribution.md5_digest)
    key.set_metadata('package', release.package.name)
    key.set_metadata('version', release.version)
    key.set_metadata('filetype', distribution.filetype)
    if distribution.pyversion:
        key.set_metadata('pyversion', distribution.pyversion)
    key.set_metadata('created', distribution.created.isoformat())

    key.set_contents_from_filename(filename=distribution.content.path,
                                   md5=_boto_md5sum(distribution.md5_digest),
                                   replace=True)

    key = bucket.new_key('releases/%s/%s' %
                         (release.package.name,
                          release.version))
    key.set_metadata('package', release.package.name)
    key.set_metadata('version', release.version)
    key.set_contents_from_string(release.metadata, replace=True)


def _boto_md5sum(digest):
    """Return the (digest, b64) pair tat boto expects"""
    return (digest,
            base64.encodestring(digest.decode('hex')).strip())


def _archive_bucket():
    """Return our S3 bucket"""
    conn = S3Connection(getattr(settings, 'AWS_ACCESS_KEY'),
                        getattr(settings, 'AWS_SECRET_KEY'))
    bucket = conn.create_bucket(getattr(settings, 'YOLAPI_ARCHIVE_BUCKET'))
    return bucket
