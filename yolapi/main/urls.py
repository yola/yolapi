from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import TemplateView

from pypi.views import index
from sync.views import sync

urlpatterns = [
    path('', index, name='index'),
    path('pypi/', include(('pypi.urls', 'pypi'), namespace='pypi')),
    path(
        'simple/',
        include(('pypi.simple.urls', 'pypi'), namespace='simple')
    ),

    path(
        'importer/',
        include(('importer.urls', 'importer'), namespace='importer')
    ),
    path('sync/', sync, name='sync'),

    path(
        'robots.txt',
        TemplateView.as_view(
            template_name='robots.txt', content_type='text/plain'
        )
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
