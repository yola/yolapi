from django.conf.urls import patterns, url

urlpatterns = patterns('yolapi.importer.views',
    url(r'^$', 'index'),
)
