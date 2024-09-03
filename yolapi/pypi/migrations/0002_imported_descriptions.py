import json
import re

from django.db import migrations


def strip_leading_spaces(apps, schema_editor):
    Release = apps.get_model("pypi", "Release")
    for release in Release.objects.all():
        if not release.metadata:
            continue
        metadata = json.loads(release.metadata)
        description = metadata.get('Description')
        if not description:
            continue
        if not re.match(r'^.+(\n {8}.*)+\n?$', description):
            continue
        fixed = re.sub(r'^ {8}', '', description, flags=re.MULTILINE)
        metadata['Description'] = fixed
        release.metadata = json.dumps(metadata)
        release.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pypi', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(strip_leading_spaces)
    ]
