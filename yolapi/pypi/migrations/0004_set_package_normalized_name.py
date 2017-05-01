# -*- coding: utf-8 -*-
from south.v2 import DataMigration


class Migration(DataMigration):
    def forwards(self, orm):
        # Replaced by 0006_re_canonicalize_names
        pass

    def backwards(self, orm):
        pass

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
            'normalized_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True'})
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
