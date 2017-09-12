from django.conf.urls import url

from importer import views as importer_views

urlpatterns = [
    url(r'^$', importer_views.index, name='index'),
]
