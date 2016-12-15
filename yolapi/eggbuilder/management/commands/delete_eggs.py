from django.core.management.base import BaseCommand, CommandError

from pypi.models import Distribution


class Command(BaseCommand):
    help = 'Delete all eggs for the specified pyverisons'
    args = '<pyversion ...>'

    def handle(self, *args, **options):
        pyversions = args
        if not pyversions:
            raise CommandError('No pyverisons specified')

        distributions = Distribution.objects.filter(pyversion__in=pyversions,
                                                    filetype='bdist_egg')
        for distribution in distributions.iterator():
            print distribution
            distribution.delete()
