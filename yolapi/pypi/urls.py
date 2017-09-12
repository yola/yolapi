from django.conf.urls import url

from pypi import views as pypi_views

urlpatterns = [
    url(r'^$', pypi_views.index, name='index'),
    url(r'^(?P<package>[\w\d_\.\-]+)/$', pypi_views.package, name='package'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-+]+)/$',
        pypi_views.release, name='release'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-+]+)'
        r'/(?P<filetype>[\w_]+)/$', pypi_views.delete, name='delete'),
    url(r'^(?P<package>[\w\d_\.\-]+)/(?P<version>[\w\d_\.\-+]+)'
        r'/(?P<filetype>[\w_]+)/(?P<pyversion>[\d.]+|any)/$',
        pypi_views.delete, name='delete'),
]
