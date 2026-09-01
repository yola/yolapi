import email.parser
import glob
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

import setuptools.archive_util
from django.core.files import File
from packaging.requirements import Requirement
from packaging.version import InvalidVersion, Version

from main import local_celery_app
from pypi.metadata import metadata_fields
from pypi.models import Package

log = logging.getLogger(__name__)

_WHEEL_PYTHON_VERSION = '3.12'
_WHEEL_PLATFORMS = (
    'manylinux_2_28_x86_64',
    'manylinux_2_17_x86_64',
    'manylinux2014_x86_64',
)


@local_celery_app.task
def ensure_requirements(requirements, recurse=True):
    """Spawn jobs to import all the specified requirements.
    """
    # We don't care about any requirement sections
    cleaned_reqs = []
    for line in requirements.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('['):
            break
        cleaned_reqs.append(line)
    requirements = '\n'.join(cleaned_reqs)

    for line in requirements.splitlines():
        if line.startswith('#'):
            continue
        requirement = Requirement(line)
        if not _meet_requirement(requirement):
            import_requirement.delay(str(requirement), recurse)


@local_celery_app.task
def import_requirement(requirement, recurse=True):
    """Import a single requirement."""
    log.info("Importing %s", requirement)
    requirement = Requirement(requirement)
    if _meet_requirement(requirement):
        return

    tmpdir = tempfile.mkdtemp(prefix='yolapi-import')
    try:
        if sdist_url := _get_sdist_url(requirement):
            _import_source(_download_into_dir(sdist_url, tmpdir), tmpdir, recurse)
    except Exception as e:
        log.exception(e)
    finally:
        shutil.rmtree(tmpdir)


def _meet_requirement(requirement):
    """Do we have the specified requirement?"""
    try:
        package = Package.objects.get(name=requirement.name)
    except Package.DoesNotExist:
        return False

    for release in package.releases.iterator():
        if requirement.specifier.contains(release.version, prereleases=True):
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

    if (
        ('Description' not in metadata)
        and (metadata_version in ('2.1', '2.2', '2.3', '2.4', '2.5'))
        and (description := parsed.get_payload())
    ):
        metadata['Description'] = description

    package, _ = Package.objects.get_or_create(name=metadata['Name'])
    release, created = package.releases.get_or_create(version=metadata['Version'])

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

    try:
        _fetch_wheel(release, metadata['Name'], metadata['Version'])
    except Exception as e:
        log.warning('No wheel for %s %s: %s', metadata['Name'], metadata['Version'], e)

    if recurse:
        reqs = []
        for line in parsed.get_all('Requires-Dist') or []:
            if 'extra ==' not in str(Requirement(line).marker or ''):
                reqs.append(line)
        if reqs:
            ensure_requirements.delay('\n'.join(reqs), recurse)


def _fetch_wheel(release, name, version):
    tmpdir = tempfile.mkdtemp(prefix='yolapi-wheel')
    platform_args = []
    for platform in _WHEEL_PLATFORMS:
        platform_args += ['--platform', platform]
    try:
        _pip_download(
            f'{name}=={version}',
            tmpdir,
            '--only-binary', ':all:',
            '--python-version', _WHEEL_PYTHON_VERSION,
            '--implementation', 'cp',
            *platform_args
        )

        wheels = glob.glob(os.path.join(tmpdir, '*.whl'))
        if not wheels:
            return
        location = wheels[0]
        filename = os.path.basename(location)
        log.info("Importing %s", filename)

        md5sum = hashlib.md5()
        with open(location, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                md5sum.update(block)
            f.seek(0)
            release.distributions.create(
                filetype='bdist_wheel',
                pyversion=filename.split('-')[-3][:16],
                md5_digest=md5sum.hexdigest(),
                content=File(f, name=filename)
            )
    finally:
        shutil.rmtree(tmpdir)


def _pip_download(spec, tmpdir, *extra_args):
    result = subprocess.run(
        [
            sys.executable, '-m', 'pip', 'download', '--no-deps', '--no-cache-dir',
            '--index-url', 'https://pypi.org/simple/',
            '--dest', tmpdir, spec, *extra_args
        ],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode:
        raise Exception(f'Failed pip download {spec}: {result.stderr.strip()[-2000:]}')


def _get_sdist_url(requirement):
    url = f'https://pypi.org/pypi/{requirement.name}/json'
    with urllib.request.urlopen(url, timeout=60) as response:
        releases = json.load(response)['releases']

    parsed_versions = []
    for version in releases:
        try:
            parsed_versions.append((Version(version), version))
        except InvalidVersion:
            continue

    for _, version in sorted(parsed_versions, reverse=True):
        if not requirement.specifier.contains(version):
            continue
        for dist in releases[version]:
            if dist['packagetype'] == 'sdist' and not dist['yanked']:
                return dist['url']
    return None


def _download_into_dir(url, tmpdir):
    path = os.path.join(tmpdir, os.path.basename(urllib.parse.urlparse(url).path))
    with urllib.request.urlopen(url, timeout=600) as response:
        with open(path, 'wb') as f:
            shutil.copyfileobj(response, f)
    return path
