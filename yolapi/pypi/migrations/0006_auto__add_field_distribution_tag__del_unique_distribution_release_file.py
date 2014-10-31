# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Distribution', fields ['release', 'filetype', 'pyversion']
        db.delete_unique('pypi_distribution', ['release_id', 'filetype', 'pyversion'])

        # Adding field 'Distribution.tag'
        db.add_column('pypi_distribution', 'tag',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=64, blank=True),
                      keep_default=False)

        # Adding unique constraint on 'Distribution', fields ['release', 'filetype', 'tag', 'pyversion']
        db.create_unique('pypi_distribution', ['release_id', 'filetype', 'tag', 'pyversion'])


    def backwards(self, orm):
        # Removing unique constraint on 'Distribution', fields ['release', 'filetype', 'tag', 'pyversion']
        db.delete_unique('pypi_distribution', ['release_id', 'filetype', 'tag', 'pyversion'])

        # Deleting field 'Distribution.tag'
        db.delete_column('pypi_distribution', 'tag')

        # Adding unique constraint on 'Distribution', fields ['release', 'filetype', 'pyversion']
        db.create_unique('pypi_distribution', ['release_id', 'filetype', 'pyversion'])


    models = {
        'pypi.distribution': {
            'Meta': {'unique_together': "(('release', 'filetype', 'pyversion', 'tag'),)", 'object_name': 'Distribution'},
            'content': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'filetype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5_digest': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'pyversion': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'distributions'", 'to': "orm['pypi.Release']"}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
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
