from django.urls import path, re_path

from pypi.simple import views as simple_views

urlpatterns = [
    path('', simple_views.index, name='index'),
    re_path(
        r'^(?P<package>[\w_.\-]+)/$', simple_views.package, name='package'),
    re_path(r'^(?P<package>[\w_.\-]+)/(?P<version>[\w_.\-]+)/$',
        simple_views.release, name='release'),
]
