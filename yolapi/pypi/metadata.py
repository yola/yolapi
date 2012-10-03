def fields(metadata_version):
    """Return meta-data about the meta-data :)"""

    if metadata_version not in ('1.0', '1.1', '1.2'):
        raise ValueError("Unknown Metadata-Version: %s" % metadata_version)

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

    return {
        'fields': fields,
        'required': required,
        'multivalued': multivalued,
        'csv': csv,
        'deprecated': deprecated,
    }
