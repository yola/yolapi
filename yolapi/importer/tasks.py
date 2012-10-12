import email.parser
import hashlib
import json
import logging
import os
import shutil
import tempfile

import celery
from django.conf import settings
from django.core.files import File
from django.core.files.storage import DefaultStorage
import pkg_resources
import setuptools.package_index
import setuptools.archive_util

from yolapi.pypi.models import Package
from yolapi.pypi.metadata import metadata_fields

log = logging.getLogger(__name__)


@celery.task(ignore_result=True)
def ensure_requirements(requirements, recurse=True):
    """Spawn jobs to import all the specified requirements.
    """
    for requirement in pkg_resources.parse_requirements(requirements):
        if not _meet_requirement(requirement):
            import_requirement.delay(str(requirement), recurse)


@celery.task(ignore_result=True)
def import_requirement(requirement, recurse=True):
    """Import a single requirement."""
    log.info("Importing %s", requirement)
    requirement = pkg_resources.Requirement.parse(requirement)
    if _meet_requirement(requirement):
        return

    pypi = setuptools.package_index.PackageIndex()
    tmpdir = tempfile.mkdtemp(prefix='yolapi-import')
    try:
        dist = pypi.fetch_distribution(requirement, tmpdir=tmpdir,
                                       force_scan=True, source=True,
                                       develop_ok=False)
        if dist is not None:
            _import_source(dist.location, tmpdir, recurse)
    except Exception, e:
        log.exception(e)
    finally:
        shutil.rmtree(tmpdir)


def _meet_requirement(requirement):
    """Do we have the specified requirement?"""
    package = Package.objects.filter(name=requirement.project_name)
    if not package.exists():
        return False

    package = package[0]
    for release in package.releases.iterator():
        dist = pkg_resources.Distribution(project_name=package.name,
                                          version=release.version)
        if dist in requirement:
            return True

    return False


def _import_source(location, tmpdir, recurse):
    """Import a source distribution"""
    log.info("Importing %s", location)
    extracted = os.path.join(tmpdir, 'extracted')
    setuptools.archive_util.unpack_archive(location, extracted)
    roots = os.listdir(extracted)
    assert len(roots) == 1
    root = os.path.join(extracted, roots[0])

    pkg_info = os.path.join(root, 'PKG-INFO')
    if not os.path.exists(pkg_info):
        raise Exception("No PKG-INFO in this sdist")

    with open(pkg_info) as f:
        parsed = email.parser.HeaderParser().parse(f)

    metadata_version = parsed.get('Metadata-Version')
    fields = metadata_fields(metadata_version)
    metadata = {}
    for field in parsed.keys():
        if field in fields['multivalued']:
            value = parsed.get_all(field)
            if value == ['UNKNOWN']:
                continue
        else:
            value = parsed.get(field)
            if value == 'UNKNOWN':
                continue
        metadata[field] = value

    package, created = Package.objects.get_or_create(name=metadata['Name'])
    release, created = package.releases.get_or_create(
            version=metadata['Version'])

    # Update metadata
    release.metadata = json.dumps(metadata)
    release.save()

    distribution = release.distributions.filter(filetype='sdist', pyversion='')
    if distribution.exists():
        raise Exception("Attempting to replace an existing sdist.")

    fs = DefaultStorage()
    fn = os.path.join(getattr(settings, 'PYPI_DISTS', 'dists'),
                      os.path.basename(location))
    if fs.exists(fn):
        log.warn(u"Removing existing file %s - this shouldn't happen", fn)
        fs.delete(fn)

    md5sum = hashlib.md5()
    with open(location) as f:
        while True:
            data = f.read(4096)
            if data == '':
                break
            md5sum.update(data)
        f.seek(0)
        md5sum = md5sum.hexdigest()

        distribution = release.distributions.create(filetype='sdist',
                                                    pyversion='',
                                                    md5_digest=md5sum,
                                                    content=File(f))
        distribution.save()
