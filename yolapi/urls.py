from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.static import static
from django.views.generic.simple import direct_to_template
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include("djangopypi.urls")),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}),
    url(r'^robots.txt$', direct_to_template,
        {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
