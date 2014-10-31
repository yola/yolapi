import logging
import re

from django.conf import settings
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import (require_http_methods, require_POST,
                                          require_safe)
from docutils.core import publish_parts

import pypi.metadata
import pypi.upload
from pypi.models import Distribution, Package, Release

log = logging.getLogger(__name__)


@require_http_methods(['HEAD', 'GET', 'POST'])
@csrf_exempt
@ensure_csrf_cookie
def index(request):
    if request.method == 'POST':
        return upload(request)
    return render_to_response('pypi/index.html', {
        'title': 'Package list',
        'packages': Package.objects.order_by('name').iterator(),
    }, context_instance=RequestContext(request))


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
    return render_to_response('pypi/package.html', {
        'title': unicode(package),
        'package': package,
    }, context_instance=RequestContext(request))


@require_safe
@ensure_csrf_cookie
def release(request, package, version):
    try:
        release = Release.objects.get(package__name=package, version=version)
    except Release.DoesNotExist:
        raise Http404

    metadata = pypi.metadata.display_sort(release.metadata_dict)

    # Flatten lists
    for i, (key, values) in enumerate(metadata):
        if isinstance(values, list):
            metadata[i] = (key, '\n'.join(values))
        if key == 'Description':
            if re.match(r'^.+(\n {8}.*)+\n?$', values):
                values = re.sub(r'^ {8}', '', values, flags=re.MULTILINE)
            values = publish_parts(
                values, writer_name='html',
                settings_overrides={'syntax_highlight': 'short'})['html_body']
            metadata[i] = (key, mark_safe(values))

    return render_to_response('pypi/release.html', {
        'title': unicode(release),
        'release': release,
        'metadata': metadata,
    }, context_instance=RequestContext(request))


@require_http_methods(['DELETE'])
def delete(request, package, version, filetype, pyversion=None, tag=None):
    if not getattr(settings, 'PYPI_ALLOW_DELETION'):
        return HttpResponseForbidden('Deletion is not allowed')

    terms = {}
    if tag:
        terms['tag'] = tag
    elif pyversion:
        terms['pyversion'] = pyversion
    try:
        distribution = Distribution.objects.get(release__package__name=package,
                                                release__version=version,
                                                filetype=filetype, **terms)
    except Distribution.DoesNotExist:
        raise Http404

    distribution.delete()

    return HttpResponse('Distribution deleted.', content_type='text/plain')
