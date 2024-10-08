from django.utils.safestring import mark_safe
from readme_renderer.markdown import render as render_markdown
from readme_renderer.rst import render as render_rst
from readme_renderer.txt import render as render_txt


def metadata_fields(metadata_version):
    """Return meta-data about the meta-data :)"""

    if metadata_version not in ('1.0', '1.1', '1.2', '2.1', '2.2', '2.3'):
        raise ValueError('Unknown Metadata-Version: %s' % metadata_version)

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
    if metadata_version in ('1.1', '1.2', '2.1', '2.2', '2.3'):
        required.update((
            'Download-URL',
        ))
        multivalued.update((
            'Classifier',
            'Requires',
            'Provides',
            'Obsoletes',
        ))
    if metadata_version in ('1.2', '2.1', '2.2', '2.3'):
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
    if metadata_version in ('2.1', '2.2', '2.3'):
        fields.update((
            'Description-Content-Type',
        ))
        multivalued.update((
            'Provides-Extra',
        ))
    if metadata_version in ('2.2', '2.3'):
        multivalued.update((
            'Dynamic',
        ))
    fields.update(required, deprecated, multivalued)

    return {
        'fields': fields,
        'required': required,
        'multivalued': multivalued,
        'csv': csv,
        'deprecated': deprecated,
    }


def display_sort(metadata):
    """Return an ordered list of key-value pairs, of a given metadata dict"""
    key_order = (
        'Name',
        'Version',
        'Summary',
        'License',
        'Home-page',
        'Project-URL',
        'Download-URL',
        'Description',
        'Description-Content-Type',
        'Author',
        'Author-email',
        'Maintainer',
        'Maintainer-email',
        'Keywords',
        'Classifier',
        'Requires-Python',
        'Requires-External',
        'Requires-Dist',
        'Requires',
        'Provides-Dist',
        'Provides',
        'Provides-Extra',
        'Obsoletes-Dist',
        'Obsoletes',
        'Platform',
        'Supported-Platform',
        'Dynamic',
        'Metadata-Version',
    )
    indices = dict((key, i) for i, key in enumerate(key_order))

    if isinstance(metadata, dict):
        metadata = metadata.items()

    return sorted(metadata, key=lambda row: (indices.get(row[0], 100), row))


def render_description(text, content_type):
    """Render Description field to HTML"""
    if content_type == 'text/x-rst':
        html = render_rst(text)
    elif content_type == 'text/markdown':
        html = render_markdown(text)
    else:
        html = render_txt(text)
    return mark_safe(html)
