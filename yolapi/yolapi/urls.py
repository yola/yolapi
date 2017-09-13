from django.conf.urls import include, url
from django.views.generic import TemplateView

from pypi.views import index
from sync.views import sync

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^pypi/', include('pypi.urls', namespace='pypi')),
    url(r'^simple/', include('pypi.simple.urls', namespace='simple')),

    url(r'^importer/', include('importer.urls', namespace='importer')),
    url(r'^sync/$', sync, name='sync'),

    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt',
                                              content_type='text/plain')),
]
