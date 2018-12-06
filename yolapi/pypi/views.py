import logging

from django.conf import settings
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden)
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import (require_http_methods, require_POST,
                                          require_safe)

from pypi.metadata import display_sort, render_description
import pypi.upload
from pypi.models import Distribution, Package, Release

log = logging.getLogger(__name__)


@require_http_methods(['HEAD', 'GET', 'POST'])
@csrf_exempt
@ensure_csrf_cookie
def index(request):
    if request.method == 'POST':
        return upload(request)
    return render(request, 'pypi/index.html', {
        'title': 'Package list',
        'packages': Package.objects.order_by('name').iterator(),
    })


@require_POST
@csrf_exempt
@ensure_csrf_cookie
def upload(request):
    if not settings.DEBUG or 'REMOTE_USER' in request.META:
        allowed_uploaders = getattr(settings, 'PYPI_ALLOWED_UPLOADERS', [])
        if request.META.get('REMOTE_USER') not in allowed_uploaders:
            return HttpResponseForbidden('You are not an authorized uploader',
                                         content_type='text/plain')
    try:
        pypi.upload.process(request)
    except pypi.upload.InvalidUpload, e:
        return HttpResponseBadRequest(unicode(e), content_type='text/plain')
    except pypi.upload.ReplacementDenied, e:
        return HttpResponseForbidden(unicode(e), content_type='text/plain')
    return HttpResponse('Accepted, thank you', content_type='text/plain')


@require_safe
@ensure_csrf_cookie
def package(request, package):
    try:
        package = Package.objects.get(name=package)
    except Package.DoesNotExist:
        raise Http404
    return render(request, 'pypi/package.html', {
        'title': unicode(package),
        'package': package,
    })


@require_safe
@ensure_csrf_cookie
def release(request, package, version):
    try:
        release = Release.objects.get(package__name=package, version=version)
    except Release.DoesNotExist:
        raise Http404

    metadata = release.metadata_dict

    # Flatten lists
    for key, values in metadata.items():
        if isinstance(values, list):
            metadata[key] = '\n'.join(values)

    if 'Description' in metadata:
        content_type = metadata.get('Description-Content-Type', 'text/x-rst')
        content_type = content_type.split(';', 1)[0]
        metadata['Description'] = render_description(
            metadata['Description'], content_type)

    return render(request, 'pypi/release.html', {
        'title': unicode(release),
        'release': release,
        'metadata': display_sort(metadata),
    })


@require_http_methods(['DELETE'])
def delete(request, package, version, filetype, pyversion=''):
    if not getattr(settings, 'PYPI_ALLOW_DELETION'):
        return HttpResponseForbidden('Deletion is not allowed')

    try:
        distribution = Distribution.objects.get(release__package__name=package,
                                                release__version=version,
                                                filetype=filetype,
                                                pyversion=pyversion)
    except Distribution.DoesNotExist:
        raise Http404

    distribution.delete()

    return HttpResponse('Distribution deleted.', content_type='text/plain')
