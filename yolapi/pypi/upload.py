import hashlib
import json
import logging

from django.conf import settings
from django.http.multipartparser import MultiPartParser

import pypi.metadata
from pypi.models import Package

log = logging.getLogger(__name__)


class CRLFParts(object):
    """A file-like object that wraps a file-like object, turning LF-delimited
    MIME headers into CRLF-delimited ones
    """
    def __init__(self, stream, boundary):
        self.boundary = boundary
        self.blocksize = 4096
        assert len(boundary) + 3 < self.blocksize

        self._buf = []  # For read()
        self._iter = self._header_transformer(self._line_iter(stream))

    def read(self, size=-1):
        """Read like a file"""
        if not self._buf:
            self._buf.append(next(self._iter, b''))
        if len(self._buf[0]) < size or size < 0:
            return self._buf.pop(0)
        block = self._buf.pop(0)
        self._buf.insert(0, block[size:])
        return block[:size]

    def _line_iter(self, stream):
        """Iterate lines from a stream, or blocks if line length is greater
        than blocksize.
        Not terribly efficient or inefficient...
        """
        buf = b''
        while True:
            if len(buf) < self.blocksize:
                buf += stream.read(self.blocksize - len(buf))
                if not buf:
                    break
            i = buf.find(b'\n')
            if i < 0:
                yield buf
                buf = b''
            else:
                yield buf[:i + 1]
                buf = buf[i + 1:]

    def _header_transformer(self, lines):
        """Transform LF in MIME headers to CRLF"""
        needle = b'--%s\n' % self.boundary
        in_header = False
        for line in lines:
            if line == needle:
                in_header = True
            if in_header:
                assert line[-1] == b'\n'
                line = line[:-1] + b'\r\n'
            if line == b'\r\n':
                in_header = False
            yield line


class InvalidUpload(Exception):
    pass


class ReplacementDenied(Exception):
    pass


def process(request):
    # Django doesn't like the LF line endings on the MIME headers that
    # distutils will give us.
    boundary = request.META['CONTENT_TYPE'].split('boundary=', 1)[1].encode()
    parser = MultiPartParser(request.META, CRLFParts(request, boundary),
                             request.upload_handlers, request.encoding)
    post, files = parser.parse()

    # Historically, the protocol field was mis-named, but twine corrected this
    protocol_version = post.get(
        'protocol_version', post.get('protcol_version', None))
    if protocol_version != '1':
        raise InvalidUpload('Missing/Invalid protocol_version')

    if post[':action'] != 'file_upload':
        raise InvalidUpload('The only supported actions are uploads')

    if '/' in files['content'].name:
        raise InvalidUpload('Invalid filename')

    if post['filetype'] not in getattr(settings, 'PYPI_ALLOWED_UPLOAD_TYPES',
                                       ('sdist',)):
        raise InvalidUpload('File type disallowed by policy')

    metadata = parse_metadata(post)

    if md5sum(files['content']) != post['md5_digest']:
        raise InvalidUpload("MD5 digest doesn't match content")

    name = post['name']
    version = post['version']

    package, _ = Package.objects.get_or_create(name=name)
    release, created = package.releases.get_or_create(version=version)

    # Update metadata
    release.metadata = json.dumps(metadata)
    release.save()

    distribution = release.distributions.filter(filetype=post['filetype'],
                                                pyversion=post['pyversion'])
    if distribution.exists():
        if not getattr(settings, 'PYPI_ALLOW_REPLACEMENT', True):
            raise ReplacementDenied(
                'A distribution with the same name and version is already '
                'present in the repository')
        distribution = distribution[0]
        distribution.delete()
        # The deletion could have garbage collected the Package and Release
        package, _ = Package.objects.get_or_create(name=name)
        release, created = package.releases.get_or_create(version=version)

    distribution = release.distributions.create(filetype=post['filetype'],
                                                pyversion=post['pyversion'],
                                                md5_digest=post['md5_digest'],
                                                content=files['content'])
    distribution.save()


def parse_metadata(post_data):
    """Parse the uploaded metadata, and return a cleaned up dictionary"""
    metadata_version = str(post_data['metadata_version'])

    try:
        fields = pypi.metadata.metadata_fields(metadata_version)
    except ValueError as e:
        raise InvalidUpload(e)

    metadata = {}
    for key in sorted(fields['fields']):
        post_key = key.lower().replace('-', '_')
        if key in fields['required'] and post_key not in post_data:
            raise InvalidUpload('Missing %s, required for Metadata-Version %s'
                                % (key, metadata_version))

        if post_data.getlist(post_key, []) in ([u'UNKNOWN'], []):
            continue

        if key in fields['multivalued']:
            metadata[key] = post_data.getlist(post_key)
        else:
            metadata[key] = post_data.get(post_key)

        # Normalise CSV fields to multi-valued
        if key in fields['csv']:
            if key in fields['multivalued']:
                metadata[key] = ','.join(metadata[key])
            metadata[key] = metadata[key].replace(';', ',')
            metadata[key] = [value.strip()
                             for value in metadata[key].split(',')
                             if value.strip()]

    return metadata


def md5sum(file_):
    """MD5Sum a UploadedFile"""
    md5 = hashlib.md5()
    for chunk in file_.chunks():
        md5.update(chunk)
    return md5.hexdigest()
