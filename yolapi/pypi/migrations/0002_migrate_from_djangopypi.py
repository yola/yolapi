import json

from django.db import IntegrityError, DatabaseError
from django.utils.datastructures import MultiValueDict
from south.db import db
from south.v2 import DataMigration

import pypi.upload


class Migration(DataMigration):

    def forwards(self, orm):
        try:
            next(orm['djangopypi.distribution'].objects.iterator())
        except DatabaseError:
            return

        for old_distribution in \
                orm['djangopypi.distribution'].objects.iterator():
            old_release = old_distribution.release
            old_package = old_release.package

            package, created = orm['pypi.package'].objects.get_or_create(
                    name=old_package.name)

            metadata = MultiValueDict(json.loads(old_release.package_info))
            metadata['metadata_version'] = old_release.metadata_version
            metadata['name'] = old_package.name
            metadata['version'] = old_release.version
            metadata = pypi.upload.parse_metadata(metadata)
            metadata = json.dumps(metadata)

            release = package.releases.filter(version=old_release.version)
            if release.exists():
                release = release[0]
                release.metadata = metadata
            else:
                release = package.releases.create(version=old_release.version,
                                                  metadata=metadata)
            release.save()

            print "Importing: %s" % (
                ', '.join((old_package.name, old_release.version,
                           old_distribution.filetype,
                           old_distribution.pyversion)))

            try:
                distribution = release.distributions.create(
                        content=old_distribution.content,
                        filetype=old_distribution.filetype,
                        md5_digest=old_distribution.md5_digest,
                        pyversion=old_distribution.pyversion,
                )
                distribution.created = old_distribution.created
                distribution.save()
            except IntegrityError:
                print "IntegrityError: Skipping"

        for table in ('auth_group',
                      'auth_group_permissions',
                      'auth_message',
                      'auth_permission',
                      'auth_user',
                      'auth_user_groups',
                      'auth_user_user_permissions',
                      'django_admin_log',
                      'django_content_type',
                      'django_session',
                      'django_site',
                      'djangopypi_classifier',
                      'djangopypi_distribution',
                      'djangopypi_masterindex',
                      'djangopypi_mirrorlog',
                      'djangopypi_mirrorlog_releases_added',
                      'djangopypi_package',
                      'djangopypi_package_maintainers',
                      'djangopypi_package_owners',
                      'djangopypi_release',
                      'djangopypi_review',
                     ):
            db.delete_table(table)

    models = {
        'pypi.distribution': {
            'Meta': {'unique_together': "(('release', 'filetype', 'pyversion'),)", 'object_name': 'Distribution'},
            'content': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'filetype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5_digest': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'pyversion': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'distributions'", 'to': "orm['pypi.Release']"})
        },
        'pypi.package': {
            'Meta': {'object_name': 'Package'},
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'primary_key': 'True'})
        },
        'pypi.release': {
            'Meta': {'unique_together': "(('package', 'version'),)", 'object_name': 'Release'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.TextField', [], {}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'releases'", 'to': "orm['pypi.Package']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'djangopypi.classifier': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Classifier'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'primary_key': 'True'})
        },
        'djangopypi.distribution': {
            'Meta': {'unique_together': "(('release', 'filetype', 'pyversion'),)", 'object_name': 'Distribution'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'content': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'filetype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5_digest': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'pyversion': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'distributions'", 'to': "orm['djangopypi.Release']"}),
            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'djangopypi.masterindex': {
            'Meta': {'object_name': 'MasterIndex'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'djangopypi.mirrorlog': {
            'Meta': {'object_name': 'MirrorLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': "'now'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': "orm['djangopypi.MasterIndex']"}),
            'releases_added': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'mirror_sources'", 'blank': 'True', 'to': "orm['djangopypi.Release']"})
        },
        'djangopypi.package': {
            'Meta': {'ordering': "['name']", 'object_name': 'Package'},
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'auto_hide': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'maintainers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'packages_maintained'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'primary_key': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'packages_owned'", 'blank': 'True', 'to': "orm['auth.User']"})
        },
        'djangopypi.release': {
            'Meta': {'ordering': "['-created']", 'unique_together': "(('package', 'version'),)", 'object_name': 'Release'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata_version': ('django.db.models.fields.CharField', [], {'default': "'1.0'", 'max_length': '64'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'releases'", 'to': "orm['djangopypi.Package']"}),
            'package_info': ('django.db.models.fields.TextField', [], {}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'djangopypi.review': {
            'Meta': {'object_name': 'Review'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.PositiveSmallIntegerField', [], {'blank': 'True'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'to': "orm['djangopypi.Release']"})
        },
    }

    complete_apps = ['pypi']
