from django.urls import path, re_path

from pypi import views as pypi_views

urlpatterns = [
    path('', pypi_views.index, name='index'),
    re_path(r'^(?P<package>[\w_.\-]+)/$', pypi_views.package, name='package'),
    re_path(r'^(?P<package>[\w_.\-]+)/(?P<version>[\w_.\-+]+)/$',
        pypi_views.release, name='release'),
    re_path(r'^(?P<package>[\w_.\-]+)/(?P<version>[\w_.\-+]+)'
        r'/(?P<filetype>[\w_]+)/$', pypi_views.delete, name='delete'),
    re_path(r'^(?P<package>[\w_.\-]+)/(?P<version>[\w_.\-+]+)'
        r'/(?P<filetype>[\w_]+)/(?P<pyversion>[\d.]+|any)/$',
        pypi_views.delete, name='delete'),
]
