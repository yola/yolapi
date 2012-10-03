import hashlib
import json

from django.conf import settings
from django.http.multipartparser import MultiPartParser

from pypi.models import Package


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
    # TODO: Validate with a form

    if md5sum(files['content']) != post['md5_digest']:
        raise InvalidUpload("MD5 digest doesn't match content")

    package = Package.objects.get_or_create(name=post['name'])[0]
    release = package.releases.get_or_create(version=post['version'])[0]

    distribution = release.distributions.filter(filetype=post['filetype'],
                                                pyversion=post['pyversion'])
    if distribution.exists():
        if not getattr(settings, 'PYPI_ALLOW_REPLACEMENT', True):
            raise ReplacementDenied(
                    "A distribution with the same name and version is already "
                    "present in the repository")
        distribution = distribution[0]
        distribution.delete()

    distribution = release.distributions.create(filetype=post['filetype'],
                                                pyversion=post['pyversion'],
                                                md5_digest=post['md5_digest'],
                                                metadata=json.dumps(post),
                                                content=files['content'])
    distribution.save()


def md5sum(file_):
    """MD5Sum a UploadedFile"""
    md5 = hashlib.md5()
    for chunk in file_.chunks():
        md5.update(chunk)
    return md5.hexdigest()
