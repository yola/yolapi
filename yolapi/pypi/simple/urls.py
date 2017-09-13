from django.conf.urls import url

from pypi.simple import views as simple_views

urlpatterns = [
    url(r'^$', simple_views.index, name='index'),
    url(r'^(?P<package>[\w\d_\.\-]+)/$', simple_views.package, name='package'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-]+)/$',
        simple_views.release, name='release'),
]
