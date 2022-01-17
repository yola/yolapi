from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_safe

from pypi.models import Package, Release


@require_safe
def index(request):
    return render(request, 'pypi.simple/index.html', {
        'title': 'Packages',
        'packages': Package.objects.iterator(),
    })


@require_safe
def package(request, package):
    try:
        package = Package.objects.get(name=package)
    except Package.DoesNotExist:
        raise Http404
    return render(request, 'pypi.simple/package.html', {
        'title': str(package),
        'package': package,
    })


@require_safe
def release(request, package, version):
    try:
        release = Release.objects.get(package__name=package, version=version)
    except Release.DoesNotExist:
        raise Http404
    return render(request, 'pypi.simple/release.html', {
        'title': str(release),
        'release': release,
    })
