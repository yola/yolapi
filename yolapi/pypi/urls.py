from django.conf.urls import patterns, url

urlpatterns = patterns('pypi.views',
    url(r'^$', 'index'),
    url(r'^(?P<package>[\w\d_\.\-]+)/$', 'package'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-+]+)/$', 'release'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-+]+)'
        r'/(?P<filetype>[\w_]+)/$', 'delete'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-+]+)'
        r'/(?P<filetype>[\w_]+)/(?P<pyversion>[\d.]+|any)/$', 'delete'),
)
