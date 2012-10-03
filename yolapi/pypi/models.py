import json
import os

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.db import models
from django.dispatch import receiver
from pkg_resources import parse_version


class Package(models.Model):
    name = models.CharField(max_length=255, unique=True, primary_key=True,
                            editable=False)

    @property
    def sorted_releases(self):
        return sorted(self.releases.iterator(),
                      key=lambda r: parse_version(r.version))

    @property
    def latest(self):
        return self.sorted_releases[-1]

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
        return json.loads(self.metadata)

    @property
    def metadata_version(self):
        return self.metadata_dict.get('Metadata-Version')

    @property
    def summary(self):
        return self.metadata_dict.get('Summary')

    def __unicode__(self):
        return u'%s %s' % (self.package.name, self.version)


class Distribution(models.Model):
    release = models.ForeignKey(Release, related_name='distributions')
    content = models.FileField(
            upload_to=getattr(settings, 'PYPI_DISTS', 'dists'), blank=False)
    md5_digest = models.CharField(max_length=32, blank=False, editable=False)
    filetype = models.CharField(max_length=32, blank=False, editable=False)
    pyversion = models.CharField(max_length=16, blank=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta(object):
        unique_together = (('release', 'filetype', 'pyversion'),)

    @property
    def path(self):
        return self.content.name

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __unicode__(self):
        return self.filename


@receiver(models.signals.pre_delete)
def distribution_delete(sender, **kwargs):
    if sender == Distribution:
        distribution = kwargs['instance']
        if distribution.path:
            archive_replaced = getattr(settings, 'PYPI_ARCHIVE', 'archive')
            if archive_replaced:
                fs = DefaultStorage()
                created = fs.created_time(distribution.content.name)
                fs.save('%s/%s-%s' % (archive_replaced,
                                      created.strftime('%Y%m%dT%H%M%SZ'),
                                      distribution.filename),
                        distribution.content)
            distribution.content.delete()
