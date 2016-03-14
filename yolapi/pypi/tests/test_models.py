from django.test import TestCase

from yolapi.pypi.models import Package


class TestPackageGet(TestCase):
    """Package.get"""

    def test_returns_package_that_matches_name(self):
        expected_package = Package.objects.create(name='package')
        found_package = Package.get('package')
        self.assertEqual(found_package, expected_package)

    def test_raises_DoesNotExist_if_not_found(self):
        with self.assertRaises(Package.DoesNotExist):
            Package.get('does not exist')

    def test_normalizes_package_name(self):
        expected_package = Package.objects.create(name='MyPackage')
        found_package = Package.get('mypackage')
        self.assertEqual(found_package, expected_package)
