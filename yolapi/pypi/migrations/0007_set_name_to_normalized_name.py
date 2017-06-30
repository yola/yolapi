# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        for package in orm['pypi.Package'].objects.all():
            # update the foreign key value on related releases since we will be
            # updating the primary key value on the Package model
            db.execute('UPDATE pypi_release SET package_id = %s '
                       'WHERE package_id = %s',
                       [package.normalized_name, package.name])
            # this is a filter then update because `name` is the primary key on
            # the Package model so Django gets confused when trying to decide
            # if it should do an insert or update since the new value for the
            # PK field does not already exist in the database
            orm['pypi.Package'].objects.filter(name=package.name).update(
                name=package.normalized_name)

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")

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
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'primary_key': 'True'}),
            'normalized_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
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
    symmetrical = True
