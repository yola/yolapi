import logging

from django.conf import settings
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (require_http_methods, require_POST,
                                          require_safe)

import yolapi.pypi.upload
import yolapi.pypi.metadata
from yolapi.pypi.models import Package, Release

log = logging.getLogger(__name__)


@require_http_methods(['HEAD', 'GET', 'POST'])
@csrf_exempt
def index(request):
    if request.method == 'POST':
        return upload(request)
    return render_to_response('yolapi.pypi/index.html', {
        'title': 'Package list',
        'packages': Package.objects.iterator(),
    }, context_instance=RequestContext(request))


@require_POST
@csrf_exempt
def upload(request):
    if not settings.DEBUG or 'REMOTE_USER' in request.META:
        allowed_uploaders = getattr(settings, 'PYPI_ALLOWED_UPLOADERS', [])
        if request.META.get('REMOTE_USER') not in allowed_uploaders:
            return HttpResponseForbidden('You are not an authorized uploader',
                                         content_type='text/plain')
    try:
        yolapi.pypi.upload.process(request)
    except yolapi.pypi.upload.InvalidUpload, e:
        return HttpResponseBadRequest(unicode(e), content_type='text/plain')
    except yolapi.pypi.upload.ReplacementDenied, e:
        return HttpResponseForbidden(unicode(e), content_type='text/plain')
    return HttpResponse('Accepted, thank you', content_type='text/plain')


@require_safe
def package(request, package):
    try:
        package = Package.objects.get(name=package)
    except Package.DoesNotExist:
        raise Http404
    return render_to_response('yolapi.pypi/package.html', {
        'title': unicode(package),
        'package': package,
    }, context_instance=RequestContext(request))


@require_safe
def release(request, package, version):
    try:
        release = Release.objects.get(package__name=package, version=version)
    except Release.DoesNotExist:
        raise Http404

    metadata = yolapi.pypi.metadata.display_sort(release.metadata_dict)

    # Flatten lists
    for i, (key, values) in enumerate(metadata):
        if isinstance(values, list):
            metadata[i] = (key, '\n'.join(values))

    return render_to_response('yolapi.pypi/release.html', {
        'title': unicode(release),
        'release': release,
        'metadata': metadata,
    }, context_instance=RequestContext(request))
