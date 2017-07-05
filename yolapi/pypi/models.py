import errno
import json
import logging
import os
import re

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import force_text
from packaging.utils import canonicalize_name
from pkg_resources import parse_version

log = logging.getLogger(__name__)


class PyPIStorage(FileSystemStorage):
    """A Storage system that archives deleted files out of the way, allowing
    new files to always have their expected filenames.
    Almost certainly a little racy"""

    def save(self, name, content):
        if self.exists(name):
            self._archive(name, unexpected=True)
        return super(PyPIStorage, self).save(name, content)

    def delete(self, name):
        if self.exists(name):
            self._archive(name)
        super(PyPIStorage, self).delete(name)

    def get_valid_name(self, name):
        # Like django.utils.get_valid_name, but allowing + too
        name = force_text(name).strip().replace(' ', '_')
        return re.sub(r'(?u)[^-\w.+]', '', name)

    def get_available_name(self, name):
        return name

    def _archive(self, name, unexpected=False):
        if unexpected:
            log.warn('Unexpectedly overwriting a file: %s', name)

        archive_replaced = getattr(settings, 'PYPI_ARCHIVE', 'archive')
        if archive_replaced:
            try:
                os.mkdir(self.path(archive_replaced))
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise

            created = self.created_time(name)
            new_name = '%s/%s-%s' % (archive_replaced,
                                     created.strftime('%Y%m%dT%H%M%SZ'),
                                     os.path.basename(name))
            log.info('Archiving %s -> %s', name, new_name)
            os.rename(self.path(name), self.path(new_name))


class Package(models.Model):
    name = models.CharField(max_length=255, unique=True, primary_key=True,
                            editable=False)
    normalized_name = models.CharField(max_length=255, unique=True,
                                       editable=False)

    @classmethod
    def get(cls, name):
        """Return package, accounting for pypi normalized package names."""
        return cls.objects.get(name=canonicalize_name(name))

    @property
    def sorted_releases(self):
        return sorted(self.releases.iterator(),
                      key=lambda r: parse_version(r.version))

    @property
    def latest(self):
        return self.sorted_releases[-1]

    def gc(self):
        if not self.releases.exists():
            self.delete()

    def save(self, *args, **kwargs):
        self.name = canonicalize_name(self.name)
        super(Package, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class Release(models.Model):
    package = models.ForeignKey(Package, related_name='releases')
    version = models.CharField(max_length=128, db_index=True, editable=False)
    metadata = models.TextField()

    class Meta(object):
        unique_together = (('package', 'version'),)

    @property
    def distribution(self):
        """Return the source upload if possible, otherwise the first upload"""
        sdist = self.distributions.filter(filetype='sdist')
        if sdist.exists():
            return sdist[0]
        dists = self.distributions
        if dists.exists():
            return dists[0]

    @property
    def metadata_dict(self):
        try:
            return json.loads(self.metadata)
        except ValueError:
            return {}

    @property
    def metadata_version(self):
        return self.metadata_dict.get('Metadata-Version')

    @property
    def summary(self):
        return self.metadata_dict.get('Summary')

    def gc(self):
        if not self.distributions.exists():
            self.delete()

    def __unicode__(self):
        return u'%s %s' % (self.package.name, self.version)


class Distribution(models.Model):
    release = models.ForeignKey(Release, related_name='distributions')
    content = models.FileField(storage=PyPIStorage(),
            upload_to=getattr(settings, 'PYPI_DISTS', 'dists'), blank=False)
    md5_digest = models.CharField(max_length=32, blank=False, editable=False)
    filetype = models.CharField(max_length=32, blank=False, editable=False)
    pyversion = models.CharField(max_length=16, blank=True, editable=False)
    created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta(object):
        unique_together = (('release', 'filetype', 'pyversion'),)

    def __init__(self, *args, **kwargs):
        self.sync_imported = kwargs.pop('sync_imported', False)
        super(Distribution, self).__init__(*args, **kwargs)

    @property
    def path(self):
        return self.content.name

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __unicode__(self):
        return self.filename

    def delete(self, *args, **kwargs):
        """Delete files off disk (not transaction-safe)"""
        self.content.delete()
        super(Distribution, self).delete(*args, **kwargs)
    delete.alters_data = True


@receiver(post_delete, sender=Distribution)
def gc_releases(sender, **kwargs):
    kwargs['instance'].release.gc()


@receiver(post_delete, sender=Release)
def gc_packages(sender, **kwargs):
    kwargs['instance'].package.gc()
