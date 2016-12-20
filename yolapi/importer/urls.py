from django.conf.urls import patterns, url

urlpatterns = patterns('importer.views',
    url(r'^$', 'index'),
)
