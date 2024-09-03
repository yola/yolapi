import email.parser
import hashlib
import json
import logging
import os
import re
import shutil
import tempfile

import pkg_resources
import setuptools.archive_util
import setuptools.package_index
from django.core.files import File

from pypi.metadata import metadata_fields
from pypi.models import Package
from yolapi import local_celery_app

log = logging.getLogger(__name__)


@local_celery_app.task
def ensure_requirements(requirements, recurse=True):
    """Spawn jobs to import all the specified requirements.
    """
    # We don't care about any requirement sections
    cleaned_reqs = []
    for line in requirements.splitlines():
        line = line.strip()
        if line.startswith('[') or not line:
            break
        cleaned_reqs.append(line)
    requirements = '\n'.join(cleaned_reqs)

    for requirement in pkg_resources.parse_requirements(requirements):
        if not _meet_requirement(requirement):
            import_requirement.delay(str(requirement), recurse)


@local_celery_app.task
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
    except Exception as e:
        log.exception(e)
    finally:
        shutil.rmtree(tmpdir)


def _meet_requirement(requirement):
    """Do we have the specified requirement?"""
    try:
        package = Package.objects.get(name=requirement.project_name)
    except Package.DoesNotExist:
        return False

    for release in package.releases.iterator():
        dist = pkg_resources.Distribution(
            project_name=requirement.project_name, version=release.version)
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
            if re.match(r'^.+(\n {8}.*)+\n?$', value):
                value = re.sub(r'^ {8}', '', value, flags=re.MULTILINE)
        metadata[field] = value

    if 'Description' not in metadata and (
            metadata_version in ('2.1', '2.2', '2.3')):
        metadata['Description'] = parsed.get_payload(decode=True)

    package, _ = Package.objects.get_or_create(name=metadata['Name'])
    release, created = package.releases.get_or_create(
            version=metadata['Version'])

    # Update metadata
    release.metadata = json.dumps(metadata)
    release.save()

    distribution = release.distributions.filter(filetype='sdist', pyversion='')
    if distribution.exists():
        raise Exception("Attempting to replace an existing sdist.")

    md5sum = hashlib.md5()
    with open(location, 'rb') as f:
        while True:
            data = f.read(4096)
            if data == b'':
                break
            md5sum.update(data)
        f.seek(0)
        md5sum = md5sum.hexdigest()

        distribution = release.distributions.create(
            filetype='sdist',
            pyversion='',
            md5_digest=md5sum,
            content=File(f, name=os.path.basename(f.name)))
        distribution.save()

    requires = os.path.join(
            root,
            '%s.egg-info' % pkg_resources.safe_name(metadata['Name']),
            'requires.txt')
    if recurse and os.path.exists(requires):
        with open(requires) as f:
            ensure_requirements.delay(f.read(), recurse)
