import django.utils.timezone
from django.db import migrations, models

import pypi.fields
import pypi.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.FileField(storage=pypi.models.PyPIStorage(), upload_to='dists')),
                ('md5_digest', models.CharField(editable=False, max_length=32)),
                ('filetype', models.CharField(editable=False, max_length=32)),
                ('pyversion', models.CharField(blank=True, editable=False, max_length=16)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('name', pypi.fields.CanonicalizedPackageNameField(editable=False, max_length=255, primary_key=True, serialize=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(db_index=True, editable=False, max_length=128)),
                ('metadata', models.TextField()),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='releases', to='pypi.Package')),
            ],
        ),
        migrations.AddField(
            model_name='distribution',
            name='release',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distributions', to='pypi.Release'),
        ),
        migrations.AlterUniqueTogether(
            name='release',
            unique_together=set([('package', 'version')]),
        ),
        migrations.AlterUniqueTogether(
            name='distribution',
            unique_together=set([('release', 'filetype', 'pyversion')]),
        ),
    ]
