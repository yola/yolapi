# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Package'
        db.create_table('pypi_package', (
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, primary_key=True)),
        ))
        db.send_create_signal('pypi', ['Package'])

        # Adding model 'Release'
        db.create_table('pypi_release', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='releases', to=orm['pypi.Package'])),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('metadata', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('pypi', ['Release'])

        # Adding unique constraint on 'Release', fields ['package', 'version']
        db.create_unique('pypi_release', ['package_id', 'version'])

        # Adding model 'Distribution'
        db.create_table('pypi_distribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('release', self.gf('django.db.models.fields.related.ForeignKey')(related_name='distributions', to=orm['pypi.Release'])),
            ('content', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('md5_digest', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('filetype', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('pyversion', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('pypi', ['Distribution'])

        # Adding unique constraint on 'Distribution', fields ['release', 'filetype', 'pyversion']
        db.create_unique('pypi_distribution', ['release_id', 'filetype', 'pyversion'])


    def backwards(self, orm):
        # Removing unique constraint on 'Distribution', fields ['release', 'filetype', 'pyversion']
        db.delete_unique('pypi_distribution', ['release_id', 'filetype', 'pyversion'])

        # Removing unique constraint on 'Release', fields ['package', 'version']
        db.delete_unique('pypi_release', ['package_id', 'version'])

        # Deleting model 'Package'
        db.delete_table('pypi_package')

        # Deleting model 'Release'
        db.delete_table('pypi_release')

        # Deleting model 'Distribution'
        db.delete_table('pypi_distribution')


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
        }
    }

    complete_apps = ['pypi']