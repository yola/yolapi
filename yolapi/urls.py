from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import direct_to_template


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'pypi.views.index', name='index'),
    url(r'^pypi/', include('pypi.urls')),
    url(r'^simple/', include('pypi.simple.urls')),
    url(r'^robots.txt$', direct_to_template,
        {'template': 'robots.txt', 'mimetype': 'text/plain'}),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
