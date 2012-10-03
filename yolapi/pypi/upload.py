import hashlib
import json
import logging
import os

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.http.multipartparser import MultiPartParser

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
            self._buf.append(next(self._iter, ''))
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
        buf = ''
        while True:
            if len(buf) < self.blocksize:
                buf += stream.read(self.blocksize - len(buf))
                if not buf:
                    break
            i = buf.find('\n')
            if i < 0:
                yield buf
                buf = ''
            else:
                yield buf[:i + 1]
                buf = buf[i + 1:]

    def _header_transformer(self, lines):
        """Transform LF in MIME headers to CRLF"""
        needle = '--%s\n' % self.boundary
        in_header = False
        for line in lines:
            if line == needle:
                in_header = True
            if in_header:
                assert line[-1] == '\n'
                line = line[:-1] + '\r\n'
            if line == '\r\n':
                in_header = False
            yield line


class InvalidUpload(Exception):
    pass


class ReplacementDenied(Exception):
    pass


def process(request):
    # Django doesn't like the LF line endings on the MIME headers that
    # distutils will give us.
    boundary = request.META['CONTENT_TYPE'].split('boundary=', 1)[1]
    parser = MultiPartParser(request.META, CRLFParts(request, boundary),
                             request.upload_handlers, request.encoding)
    post, files = parser.parse()

    if post.get('protcol_version', None) != '1':
        raise InvalidUpload("Missing/Invalid protcol_version")

    if post[':action'] != 'file_upload':
        raise InvalidUpload("The only supported actions are uploads")

    if '/' in files['content'].name:
        raise InvalidUpload("Invalid filename")

    metadata = parse_metadata(post)

    if md5sum(files['content']) != post['md5_digest']:
        raise InvalidUpload("MD5 digest doesn't match content")

    package, created = Package.objects.get_or_create(name=post['name'])
    release, created = package.releases.get_or_create(version=post['version'])

    # Update metadata
    release.metadata = json.dumps(metadata)
    release.save()

    distribution = release.distributions.filter(filetype=post['filetype'],
                                                pyversion=post['pyversion'])
    if distribution.exists():
        if not getattr(settings, 'PYPI_ALLOW_REPLACEMENT', True):
            raise ReplacementDenied(
                    "A distribution with the same name and version is already "
                    "present in the repository")
        distribution = distribution[0]
        distribution.delete()

    fs = DefaultStorage()
    fn = os.path.join(getattr(settings, 'PYPI_DISTS', 'dists'),
                      files['content'].name)
    if fs.exists(fn):
        log.warn("Removing existing file %s - this shouldn't happen", fn)
        fs.delete(fn)

    distribution = release.distributions.create(filetype=post['filetype'],
                                                pyversion=post['pyversion'],
                                                md5_digest=post['md5_digest'],
                                                content=files['content'])
    distribution.save()


def parse_metadata(post_data):
    """Parse the uploaded metadata, and return a cleaned up dictionary"""
    metadata_version = str(post_data['metadata_version'])

    if metadata_version not in ('1.0', '1.1', '1.2'):
        raise InvalidUpload("Unknown Metadata-Version: %s" % metadata_version)

    required = set((
        'Metadata-Version',
        'Name',
        'Summary',
        'Version',
    ))
    fields = set((
        'Author',
        'Author-email',
        'Description',
        'Home-page',
        'Keywords',
        'License',
    ))
    multivalued = set((
        'Platform',
        'Supported-Platform',
    ))
    csv = set((
        'Platform',
        'Keywords',
    ))
    deprecated = set()

    if metadata_version in ('1.0', '1.1'):
        required.update((
            'Author-email',
            'License',
        ))
    if metadata_version in ('1.1', '1.2'):
        required.update((
            'Download-URL',
        ))
        multivalued.update((
            'Classifier',
            'Requires',
            'Provides',
            'Obsoletes',
        ))
    if metadata_version in ('1.2',):
        required.update((
            'Requires-Python',
        ))
        deprecated.update((
            'Requires',
            'Provides',
            'Obsoletes',
        ))
        fields.update((
            'Maintainer',
            'Maintainer-email',
        ))
        multivalued.update((
            'Obsoletes-Dist',
            'Project-URL',
            'Provides-Dist',
            'Requires-Dist',
            'Requires-External',
        ))
    fields.update(required, deprecated, multivalued)

    metadata = {}
    for key in sorted(fields):
        post_key = key.lower().replace('-', '_')
        if key in required and post_key not in post_data:
            raise InvalidUpload("Missing %s, required for Metadata-Version %s"
                                % (key, metadata_version))

        if post_data.getlist(post_key, []) in ([u'UNKNOWN'], []):
            continue

        if key in multivalued:
            metadata[key] = post_data.getlist(post_key)
        else:
            metadata[key] = post_data.get(post_key)

        if key in csv:
            if key in multivalued:
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
