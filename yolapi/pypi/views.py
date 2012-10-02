import logging

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (require_http_methods, require_POST,
                                          require_safe)

import pypi.upload
from pypi.models import Package, Release

log = logging.getLogger(__name__)


@require_http_methods(['HEAD', 'GET', 'POST'])
@csrf_exempt
def index(request):
    if request.method == 'POST':
        return upload(request)
    return render_to_response('index.html', {
        'title': 'Package list',
        'packages': Package.objects.iterator(),
    }, context_instance=RequestContext(request))


@require_POST
@csrf_exempt
def upload(request):
    status = 500
    if pypi.upload.process(request):
        status = 200
    return HttpResponse(status=status)


@require_safe
def package(request, package):
    try:
        package = Package.objects.get(name=package)
    except Package.DoesNotExist:
        raise Http404
    return render_to_response('package.html', {
        'title': unicode(package),
        'package': package,
    }, context_instance=RequestContext(request))


@require_safe
def release(request, package, version):
    try:
        release = Release.objects.get(package__name=package, version=version)
    except Release.DoesNotExist:
        raise Http404
    return render_to_response('release.html', {
        'title': unicode(release),
        'release': release,
    }, context_instance=RequestContext(request))
