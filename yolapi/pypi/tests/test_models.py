from django.test import TestCase

from pypi.models import Package


class TestPackage(TestCase):
    def test_normalizes_name_on_save(self):
        package = Package(name='AN_aWesome-pack_agE')
        package.save()
        self.assertEqual(package.name, 'an-awesome-pack-age')


class TestPackageGet(TestCase):
    """Package.get"""

    def test_normalizes_name_when_getting_package(self):
        expected_package = Package.objects.create(name='my-package')
        found_package = Package.get('My_Package')
        self.assertEqual(found_package, expected_package)

    def test_raises_DoesNotExist_if_not_found(self):
        with self.assertRaises(Package.DoesNotExist):
            Package.get('does not exist')


class TestPackageGetOrCreate(TestCase):
    """Package.get_or_create"""

    def test_creates_package_if_existing_package_not_found(self):
        package, created = Package.get_or_create('My_Package')
        self.assertTrue(created)
        self.assertEqual(package.name, 'my-package')

    def test_returns_existing_package_if_found(self):
        existing_package = Package.objects.create(name='find-me')
        package, created = Package.get_or_create('Find_Me')
        self.assertEqual(package, existing_package)
        self.assertFalse(created)
