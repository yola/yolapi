from django.core.management.base import BaseCommand

import eggbuilder.tasks


class Command(BaseCommand):
    help = 'Build all missing eggs'

    def handle(self, *args, **options):
        eggbuilder.tasks.build_missing_eggs.delay()
        print "Scheduled egg builds"
