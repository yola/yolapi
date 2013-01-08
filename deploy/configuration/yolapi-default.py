import os

from yola.configurator.dicts import MissingValue, merge_dicts


def update(config):
    data_path = os.path.join(config.deploy.root, 'yolapi', 'data')
    new = {
        'yolapi': {
            'allowed_uploaders': ['yola'],
            'build_eggs_for': ['2.6'],
            'aws': {
                'accesskey': MissingValue('yolapi.aws.accesskey'),
                'secretkey': MissingValue('yolapi.aws.secretkey'),
                'archive_bucket': 'yolapi.%s' % config.common.domain.services,
            },
            'debug': False,
            'template_debug': False,
            'path': {
                'data': data_path,
                'log': '/var/log/yolapi.log',
                'celery_log': '/var/log/yolapi-worker.log',
            },
            'ssl': {
                'cert': MissingValue('yolapi.ssl.cert'),
                'key': MissingValue('yolapi.ssl.key'),
            },
            'domain': 'yolapi.%s' % config.common.domain.services,
            'db':  {
                'name': os.path.join(data_path, 'yolapi.sqlite'),
                'engine': 'django.db.backends.sqlite3',
                'user': '',
                'password': '',
                'host': '',
                'port': '',
            },
            'sentry_dsn': '',
        },
    }
    return merge_dicts(config, new)
