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

from pypi.models import Distribution

log = logging.getLogger(__name__)


@celery.task(ignore_result=True)
def build_missing_eggs():
    pyversions = getattr(settings, 'PYPI_EGG_PYVERSIONS', [])
    if not pyversions:
        return

    distributions = Distribution.objects.filter(filetype='sdist')
    for distribution in distributions.iterator():
        release = distribution.release
        for pyversion in pyversions:
            egg = release.distributions.filter(filetype='bdist_egg',
                                               pyversion=pyversion)
            if not egg.exists():
                build_egg.delay(release.package.name, release.version,
                                pyversion)


@celery.task(ignore_result=True)
def build_egg(package, version, pyversion):
    distributions = Distribution.objects.filter(release__package__name=package,
                                                release__version=version)
    eggs = distributions.filter(filetype='bdist_egg', pyversion=pyversion)
    if eggs.exists():
        log.info('Egg already exists for %s==%s', package, version)
        return
    distributions = distributions.filter(filetype='sdist')
    if not distributions.exists():
        log.error('Unable to find source distribution for %s==%s',
                  package, version)
        return
    distribution = distributions[0]
    release = distribution.release

    tmpdir = tempfile.mkdtemp(prefix='yolapi-eggbuilder')
    try:
        setuptools.archive_util.unpack_archive(distribution.content.path,
                                               tmpdir)
        roots = os.listdir(tmpdir)
        assert len(roots) == 1
        root = os.path.join(tmpdir, roots[0])

        try:
            subprocess.check_call((
                'python%s' % pyversion,
                '-c', 'import sys, setuptools; sys.argv[0] = "setup.py"; '
                      '__file__ = "setup.py"; execfile(__file__)',
                'bdist_egg'), cwd=root)
        except subprocess.CalledProcessError:
            log.error('Unable to build %s==%s', package, version)
            return

        egg = '%s-%s-py%s.egg' % (
                pkg_resources.to_filename(pkg_resources.safe_name(package)),
                pkg_resources.to_filename(pkg_resources.safe_version(version)),
                pyversion)
        egg = os.path.join(root, 'dist', egg)

        if not os.path.exists(egg):
            egg = (egg.rsplit('.', 1)[0]
                   + '-%s.egg' % pkg_resources.get_build_platform())

        if not os.path.exists(egg):
            log.warn("We couldn't guess the egg name for %s==%s",
                     package, version)

            egg = glob.glob(os.path.join(root, 'dist', '*.egg'))
            assert len(egg) == 1
            egg = egg[0]

        md5sum = hashlib.md5()
        with open(egg) as f:
            while True:
                data = f.read(4096)
                if data == '':
                    break
                md5sum.update(data)
            f.seek(0)
            md5sum = md5sum.hexdigest()

            distribution = release.distributions.create(filetype='bdist_egg',
                                                        pyversion=pyversion,
                                                        md5_digest=md5sum,
                                                        content=File(f))
            distribution.save()
    finally:
        shutil.rmtree(tmpdir)
