import logging
import urllib

import boto3
import dateutil.parser
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files import File

from pypi.models import Distribution, Package
from yolapi import local_celery_app

log = logging.getLogger(__name__)
allow_replacement = getattr(settings, 'PYPI_ALLOW_REPLACEMENT', True)


@local_celery_app.task
def sync():
    """Spawn jobs to perform a 2-way sync with S3.
    Relies on timestamps, if there are conflicts, probably pretty racey...
    """
    bucket = _bucket()

    s3_distributions = {}
    for s3_obj_summary in bucket.objects.filter(
            Delimiter='/', Prefix='dists/'):
        s3_distributions[s3_obj_summary.key.split(u'/', 1)[1]] = s3_obj_summary

    # Our Distribution table doesn't store the bare filename, but we're about
    # to do a full table scan, so no loss...
    by_filename = {}

    for distribution in Distribution.objects.all():
        by_filename[distribution.filename] = distribution.id

        if distribution.filename not in s3_distributions:
            log.info(u"Queueing push: %s [missing]", distribution.filename)
            push.delay(distribution.id)
            continue

        s3_obj_summary = s3_distributions[distribution.filename]
        if allow_replacement and _compare_db_with_s3_obj_summary(
                distribution, s3_obj_summary) > 0:
            log.info(u"Queueing push: %s [mismatch]", distribution.filename)
            push.delay(distribution.id)

    for filename, s3_obj_summary in s3_distributions.iteritems():
        if filename not in by_filename:
            log.info(u"Queueing pull: %s [missing]", filename)
            pull.delay(filename)
            continue

        distribution = Distribution.objects.get(id=by_filename[filename])
        if allow_replacement and _compare_db_with_s3_obj_summary(
                distribution, s3_obj_summary) < 0:
            log.info(u"Queueing pull %s [mismatch]", filename)
            pull.delay(filename)


@local_celery_app.task
def push(id):
    """Push a Distribution to S3, and update its metadata"""
    distribution = Distribution.objects.get(id=id)
    release = distribution.release
    log.info(u"Pushing %s", distribution.filename)

    bucket = _bucket()
    s3_obj = bucket.Object(u'dists/{}'.format(distribution.filename))
    try:
        s3_obj.load()
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            raise
    else:
        if not allow_replacement:
            log.warn("Aborting replacement")
            return
        if _compare_db_with_s3_obj(distribution, s3_obj) <= 0:
            log.warn("Aborting push on top of a newer object")
            return

    metadata = {
        'md5_digest': distribution.md5_digest,
        'package': release.package.name,
        'version': release.version,
        'filetype': distribution.filetype,
        'uploaded': urllib.quote(distribution.created.isoformat())
    }
    if distribution.pyversion:
        metadata['pyversion'] = distribution.pyversion

    s3_obj.put(
        Body=distribution.content,
        ContentMD5=_boto3_md5sum(distribution.md5_digest),
        Metadata=metadata,
    )

    bucket.Object(
        u'releases/{}/{}'.format(release.package.name, release.version)
    ).put(
        Body=release.metadata,
        Metadata={
            'package': release.package.name,
            'version': release.version,
        }
    )


@local_celery_app.task
def pull(filename):
    """Pull a Distribution from S3"""
    log.info(u"Pulling %s", filename)

    bucket = _bucket()
    s3_obj = bucket.Object(u'dists/{}'.format(filename))
    try:
        s3_obj.load()
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            log.warn('Aborting pull of non-existent file')
            return
        raise

    package = s3_obj.metadata['package']
    version = s3_obj.metadata['version']
    filetype = s3_obj.metadata['filetype']
    pyversion = s3_obj.metadata.get('pyversion', u'')
    md5_digest = s3_obj.metadata['md5_digest']
    uploaded = dateutil.parser.parse(
        urllib.unquote(s3_obj.metadata['uploaded']))

    package, _ = Package.objects.get_or_create(name=package)
    release, created = package.releases.get_or_create(version=version)
    distribution = release.distributions.filter(filetype=filetype,
                                                pyversion=pyversion)
    if distribution.exists():
        distribution = distribution[0]
        if not allow_replacement:
            log.warn("Aborting replacement")
            return
        if _compare_db_with_s3_obj(distribution, s3_obj) >= 0:
            log.warn("Aborting pull on top of a newer object")
            return
        distribution.delete()
        # The deletion could have garbage collected the Package and Release
        package, _ = Package.objects.get_or_create(name=package)
        release, created = package.releases.get_or_create(version=version)

    distribution = release.distributions.create(
        filetype=filetype,
        pyversion=pyversion,
        md5_digest=md5_digest,
        content=File(s3_obj.get()['Body'], name=filename),
        created=uploaded,
        sync_imported=True)
    distribution.save()

    s3_obj = bucket.Object(u'releases/{}/{}'.format(
        release.package.name, release.version))
    release.metadata = s3_obj.get()['Body'].read().decode('utf-8')
    release.save()


def _boto3_md5sum(digest):
    """Return the b64 that boto3 expects"""
    return digest.decode('hex').encode('base64').strip()


def _compare_db_with_s3_obj_summary(distribution, s3_obj_summary):
    s3_md5 = s3_obj_summary.e_tag.strip('"')
    if s3_md5 == distribution.md5_digest:
        return 0

    return _compare_db_with_s3_obj(distribution, s3_obj_summary.Object())


def _compare_db_with_s3_obj(distribution, s3_obj):
    """Compare a Distribution with an S3 obj
    Returns:
        < 0: S3 Newer
        0:   equal
        > 0: Distribution newer
    """
    s3_md5 = s3_obj.e_tag.strip('"')
    if s3_md5 == distribution.md5_digest:
        return 0

    created = dateutil.parser.parse(
        urllib.unquote(s3_obj.metadata['uploaded']))
    return cmp(distribution.created, created)


def _bucket():
    """Return our S3 bucket"""
    global _cached_bucket
    if _cached_bucket is None:
        bucket_name = settings.PYPI_SYNC_BUCKET
        if not bucket_name:
            raise Exception("Syncing is disabled")

        s3 = boto3.resource(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION_NAME,
        )
        _cached_bucket = s3.Bucket(bucket_name)
        if not _cached_bucket.creation_date:
            _cached_bucket = s3.create_bucket(Bucket=bucket_name)
    return _cached_bucket


_cached_bucket = None
