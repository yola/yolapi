from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include("djangopypi.urls")),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
