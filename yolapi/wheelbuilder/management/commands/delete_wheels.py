from django.core.management.base import BaseCommand, CommandError

from pypi.models import Distribution


class Command(BaseCommand):
    help = 'Delete all wheels for the specified tags'
    args = '<tag ...>'

    def handle(self, *args, **options):
        tags = args
        if not tags:
            raise CommandError('No tags specified')

        distributions = Distribution.objects.filter(tag__in=tags,
                                                    filetype='bdist_wheel')
        for distribution in distributions.iterator():
            print distribution
            distribution.delete()
