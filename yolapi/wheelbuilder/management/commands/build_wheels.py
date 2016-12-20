from django.core.management.base import BaseCommand

import wheelbuilder.tasks


class Command(BaseCommand):
    help = 'Build all missing wheels'

    def handle(self, *args, **options):
        wheelbuilder.tasks.build_missing_wheels.delay()
        print "Scheduled wheel builds"
