import base64
import dateutil.parser
import logging
import urllib

import boto.s3.connection
from celery import task
from django.conf import settings
from django.core.files import File

from pypi.models import Distribution, Package

log = logging.getLogger(__name__)
allow_replacement = getattr(settings, 'PYPI_ALLOW_REPLACEMENT', True)


@task(ignore_result=True)
def sync():
    """Spawn jobs to perform a 2-way sync with S3.
    Relies on timestamps, if there are conflicts, probably pretty racey...
    """
    bucket = _bucket()

    s3_distributions = {}
    for key in bucket.list(delimiter='/', prefix='dists/'):
        if isinstance(key, boto.s3.key.Key):
            s3_distributions[key.name.split(u'/', 1)[1]] = key

    # Our Distribution table doesn't store the bare filename, but we're about
    # to do a full table scan, so no loss...
    by_filename = {}

    for distribution in Distribution.objects.all():
        by_filename[distribution.filename] = distribution.id

        if distribution.filename not in s3_distributions:
            log.info(u"Queueing push: %s [missing]", distribution.filename)
            push.delay(distribution.id)
            continue

        key = s3_distributions[distribution.filename]
        if allow_replacement and _compare_db_with_s3(distribution, key) > 0:
            log.info(u"Queueing push: %s [mismatch]", distribution.filename)
            push.delay(distribution.id)

    for filename, key in s3_distributions.iteritems():
        if filename not in by_filename:
            log.info(u"Queueing pull: %s [missing]", filename)
            pull.delay(filename)
            continue

        distribution = Distribution.objects.get(id=by_filename[filename])
        if allow_replacement and _compare_db_with_s3(distribution, key) < 0:
            log.info(u"Queueing pull %s [mismatch]", filename)
            pull.delay(filename)


@task(ignore_result=True)
def push(id):
    """Push a Distribution to S3, and update its metadata"""
    distribution = Distribution.objects.get(id=id)
    release = distribution.release
    log.info(u"Pushing %s", distribution.filename)

    bucket = _bucket()
    key = bucket.get_key(u'dists/%s' % distribution.filename)
    if key is not None:
        if not allow_replacement:
            log.warn("Aborting replacement")
            return
        if _compare_db_with_s3(distribution, key) <= 0:
            log.warn("Aborting push on top of a newer object")
            return

    key = bucket.new_key(u'dists/%s' % distribution.filename)

    key.set_metadata('md5_digest', distribution.md5_digest)
    key.set_metadata('package', release.package.name)
    key.set_metadata('version', release.version)
    key.set_metadata('filetype', distribution.filetype)
    uploaded = urllib.quote(distribution.created.isoformat())
    key.set_metadata('uploaded', uploaded)
    if distribution.pyversion:
        key.set_metadata('pyversion', distribution.pyversion)

    key.set_contents_from_filename(filename=distribution.content.path,
                                   md5=_boto_md5sum(distribution.md5_digest),
                                   replace=True)

    key = bucket.new_key(u'releases/%s/%s' %
                         (release.package.name,
                          release.version))
    key.set_metadata('package', release.package.name)
    key.set_metadata('version', release.version)
    key.set_contents_from_string(release.metadata, replace=True)


@task(ignore_result=True)
def pull(filename):
    """Pull a Distribution from S3"""
    log.info(u"Pulling %s", filename)

    bucket = _bucket()
    key = bucket.get_key(u'dists/%s' % filename)
    if key is None:
        log.warn('Aborting pull of non-existent file')
        return

    package = key.get_metadata('package')
    version = key.get_metadata('version')
    filetype = key.get_metadata('filetype')
    pyversion = key.get_metadata('pyversion') or u''
    md5_digest = key.get_metadata('md5_digest')
    uploaded = dateutil.parser.parse(key.get_metadata('uploaded'))

    try:
        package = Package.get(package)
    except Package.DoesNotExist:
        package = Package.objects.create(name=package)
    release, created = package.releases.get_or_create(version=version)
    distribution = release.distributions.filter(filetype=filetype,
                                                pyversion=pyversion)
    if distribution.exists():
        distribution = distribution[0]
        if not allow_replacement:
            log.warn("Aborting replacement")
            return
        if _compare_db_with_s3(distribution, key) >= 0:
            log.warn("Aborting pull on top of a newer object")
            return
        distribution.delete()
        # The deletion could have garbage collected the Package and Release
        try:
            package = Package.get(package)
        except Package.DoesNotExist:
            package = Package.objects.create(name=package)
        release, created = package.releases.get_or_create(version=version)

    distribution = release.distributions.create(filetype=filetype,
                                                pyversion=pyversion,
                                                md5_digest=md5_digest,
                                                content=File(key),
                                                created=uploaded,
                                                sync_imported=True)
    distribution.save()

    key = bucket.get_key(u'releases/%s/%s' %
                         (release.package.name,
                          release.version))
    release.metadata = key.get_contents_as_string()
    release.save()


def _boto_md5sum(digest):
    """Return the (digest, b64) pair tat boto expects"""
    return (digest,
            base64.encodestring(digest.decode('hex')).strip())


def _compare_db_with_s3(distribution, key):
    """Compare a Distribution with an S3 key
    Returns:
        < 0: S3 Newer
        0:   equal
        > 0: Distribution newer
    """
    s3_md5 = key.etag.strip('"')
    if (s3_md5 == distribution.md5_digest):
        return 0

    if not key.metadata:
        bucket = _bucket()
        key = bucket.get_key(key.name)

    created = dateutil.parser.parse(key.get_metadata('uploaded'))
    return cmp(distribution.created, created)


def _bucket():
    """Return our S3 bucket"""
    global _cached_bucket
    if _cached_bucket is None:
        credentials = (getattr(settings, 'AWS_ACCESS_KEY'),
                       getattr(settings, 'AWS_SECRET_KEY'))
        bucket_name = getattr(settings, 'PYPI_SYNC_BUCKET')
        if not bucket_name:
            raise Exception("Syncing is disabled")

        conn = boto.s3.connection.S3Connection(*credentials)
        try:
            _cached_bucket = conn.get_bucket(bucket_name)
        except boto.exception.S3ResponseError:
            _cached_bucket = conn.create_bucket(bucket_name)
    return _cached_bucket

_cached_bucket = None
