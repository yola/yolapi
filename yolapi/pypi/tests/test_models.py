from django.test import TestCase

from yolapi.pypi.models import Package

class TestPackage(TestCase):
    def test_sets_normalized_name_on_save(self):
        package = Package(name='AN_aWesome-pack_agE')
        package.save()
        self.assertEqual(package.normalized_name, 'an-awesome-pack-age')


class TestPackageGet(TestCase):
    """Package.get"""

    def test_returns_package_that_matches_name(self):
        expected_package = Package.objects.create(name='package')
        found_package = Package.get('package')
        self.assertEqual(found_package, expected_package)

    def test_raises_DoesNotExist_if_not_found(self):
        with self.assertRaises(Package.DoesNotExist):
            Package.get('does not exist')

    def test_finds_package_using_normalized_name(self):
        expected_package = Package.objects.create(name='My_Package-foo')
        found_package = Package.get('my-package-foo')
        self.assertEqual(found_package, expected_package)
