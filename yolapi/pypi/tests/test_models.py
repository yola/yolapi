from django.test import TestCase

from pypi.models import Package


class TestPackage(TestCase):
    def setUp(self):
        self.package = Package.objects.create(name='AN_aWesome-pack_agE')

    def test_normalizes_name_on_save(self):
        self.assertEqual(self.package.name, 'an-awesome-pack-age')

    def test_nomalizes_name_before_lookups(self):
        packages = Package.objects.filter(name='An_AwEsome-Pack_agE')
        self.assertEqual(packages[0], self.package)
