import os

from yoconfigurator.dicts import merge_dicts


def update(config):
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..', '..', 'data'))
    new = {
        'yolapi': {
            'debug': True,
            'template_debug': True,
            'path': {
                'data': data_path,
                'log': os.path.join(data_path, 'yolapi.log'),
            },
            'db': {
                'name': os.path.join(data_path, 'yolapi.sqlite'),
            },
            'sentry_dsn': ''
        },
    }
    return merge_dicts(config, new)
