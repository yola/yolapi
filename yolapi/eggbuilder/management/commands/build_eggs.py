from django.core.management.base import BaseCommand

import yolapi.eggbuilder.tasks


class Command(BaseCommand):
    help = 'Build eggs'

    def handle(self, *args, **options):
        yolapi.eggbuilder.tasks.build_missing_eggs.delay()
        print "Scheduled egg builds"
