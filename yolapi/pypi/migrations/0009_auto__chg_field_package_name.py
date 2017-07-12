# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Package.name'
        db.alter_column('pypi_package', 'name', self.gf('pypi.fields.CanonicalizedPackageNameField')(unique=True, max_length=255, primary_key=True))

    def backwards(self, orm):

        # Changing field 'Package.name'
        db.alter_column('pypi_package', 'name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, primary_key=True))

    models = {
        'pypi.distribution': {
            'Meta': {'unique_together': "(('release', 'filetype', 'pyversion'),)", 'object_name': 'Distribution'},
            'content': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'filetype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5_digest': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'pyversion': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'distributions'", 'to': "orm['pypi.Release']"})
        },
        'pypi.package': {
            'Meta': {'object_name': 'Package'},
            'name': ('pypi.fields.CanonicalizedPackageNameField', [], {'unique': 'True', 'max_length': '255', 'primary_key': 'True'})
        },
        'pypi.release': {
            'Meta': {'unique_together': "(('package', 'version'),)", 'object_name': 'Release'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.TextField', [], {}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'releases'", 'to': "orm['pypi.Package']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'})
        }
    }

    complete_apps = ['pypi']