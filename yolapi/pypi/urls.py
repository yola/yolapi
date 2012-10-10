from django.conf.urls import patterns, url

urlpatterns = patterns('yolapi.pypi.views',
    url(r'^$', 'index'),
    url(r'^(?P<package>[\w\d_\.\-]+)/$', 'package'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/$', 'release'),
)
