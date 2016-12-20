import hashlib
import glob
import logging
import os
import shutil
import subprocess
import tempfile

import celery
import pkg_resources
import setuptools.archive_util
from django.conf import settings
from django.core.files import File
from django.db.models import Q

from pypi.models import Distribution

log = logging.getLogger(__name__)


@celery.task(ignore_result=True)
def build_missing_wheels():
    tags = getattr(settings, 'PYPI_WHEEL_TAGS', [])
    if not tags:
        return

    distributions = Distribution.objects.filter(filetype='sdist')
    for distribution in distributions.iterator():
        release = distribution.release
        for tag in tags:
            wheel = release.distributions.filter(
                Q(tag=tag) | Q(tag='py2-none-any') | Q(tag='py2.py3-none-any'),
                filetype='bdist_wheel')
            if not wheel.exists():
                build_wheel.delay(release.package.name, release.version,
                                  tag)


@celery.task(ignore_result=True)
def build_wheel(package, version, tag):
    distributions = Distribution.objects.filter(release__package__name=package,
                                                release__version=version)
    wheels = distributions.filter(filetype='bdist_wheel', tag=tag)
    if wheels.exists():
        log.info('Wheel already exists for %s==%s', package, version)
        return
    distributions = distributions.filter(filetype='sdist')
    if not distributions.exists():
        log.error('Unable to find source distribution for %s==%s',
                  package, version)
        return
    distribution = distributions[0]
    release = distribution.release

    tmpdir = tempfile.mkdtemp(prefix='yolapi-wheelbuilder')
    try:
        setuptools.archive_util.unpack_archive(distribution.content.path,
                                               tmpdir)
        roots = os.listdir(tmpdir)
        assert len(roots) == 1
        root = os.path.join(tmpdir, roots[0])

        try:
            subprocess.check_call((
                'python%s' % tag,
                '-c', 'import sys, setuptools; sys.argv[0] = "setup.py"; '
                      '__file__ = "setup.py"; execfile(__file__)',
                'bdist_wheel'), cwd=root)
        except subprocess.CalledProcessError:
            log.error('Unable to build %s==%s', package, version)
            return

        wheel = '%s-%s-py%s.whl' % (
                pkg_resources.to_filename(pkg_resources.safe_name(package)),
                pkg_resources.to_filename(pkg_resources.safe_version(version)),
                tag)
        wheel = os.path.join(root, 'dist', wheel)

        if not os.path.exists(wheel):
            wheel = (wheel.rsplit('.', 1)[0]
                   + '-%s.whl' % pkg_resources.get_build_platform())

        if not os.path.exists(wheel):
            log.warn("We couldn't guess the wheel name for %s==%s",
                     package, version)

            wheel = glob.glob(os.path.join(root, 'dist', '*.whl'))
            assert len(wheel) == 1
            wheel = wheel[0]

        md5sum = hashlib.md5()
        with open(wheel) as f:
            while True:
                data = f.read(4096)
                if data == '':
                    break
                md5sum.update(data)
            f.seek(0)
            md5sum = md5sum.hexdigest()

            distribution = release.distributions.create(filetype='bdist_wheel',
                                                        tag=tag,
                                                        md5_digest=md5sum,
                                                        content=File(f))
            distribution.save()
    finally:
        shutil.rmtree(tmpdir)
