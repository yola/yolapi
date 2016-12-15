from django.http import Http404
from django.test import RequestFactory, TestCase

from pypi.models import Package
from pypi.simple.views import package


class TestPackageView(TestCase):
    def test_renders_requested_package(self):
        Package.objects.create(name='the-name-of-my-package')
        request = RequestFactory().get('/simple/the-name-of-my-package')
        response = package(request, 'the-name-of-my-package')
        self.assertEqual(response.status_code, 200)
        self.assertIn('the-name-of-my-package', response.content)

    def test_404s_if_package_name_not_found(self):
        request = RequestFactory().get('/simple/does-not-exist')
        with self.assertRaises(Http404):
            package(request, 'does-not-exist')
