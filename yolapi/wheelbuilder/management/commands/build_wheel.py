import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from pypi.models import Package
import wheelbuilder.tasks


class Command(BaseCommand):
    help = 'Build a particualar wheel (in the foreground)'
    args = '<package> [<version>]'
    option_list = BaseCommand.option_list + (
        make_option('--tag',
                    default='.'.join(str(v) for v in sys.version_info[:2]),
                    help='The version of the Python to build with'),
    )

    def handle(self, *args, **options):
        if len(args) < 0 or len(args) > 2:
            raise CommandError('Expected 1-2 arguments')

        package = args[0]

        if len(args) > 1:
            version = args[1]
        else:
            packages = Package.objects.filter(name=package)
            if not packages.exists():
                raise CommandError('Unknown package: %s' % package)
            version = packages[0].latest.version

        tag = options['tag']

        wheelbuilder.tasks.build_wheel(package, version, tag)
