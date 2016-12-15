from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_safe

from pypi.models import Package, Release


@require_safe
def index(request):
    return render_to_response('pypi.simple/index.html', {
        'title': 'Packages',
        'packages': Package.objects.iterator(),
    }, context_instance=RequestContext(request))


@require_safe
def package(request, package):
    try:
        package = Package.get(package)
    except Package.DoesNotExist:
        raise Http404
    return render_to_response('pypi.simple/package.html', {
        'title': unicode(package),
        'package': package,
    }, context_instance=RequestContext(request))


@require_safe
def release(request, package, version):
    try:
        release = Release.objects.get(package__name=package, version=version)
    except Release.DoesNotExist:
        raise Http404
    return render_to_response('pypi.simple/release.html', {
        'title': unicode(release),
        'release': release,
    }, context_instance=RequestContext(request))
