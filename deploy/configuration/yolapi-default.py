#!/usr/bin/env python

import json
import os
import sys

try:
    from lib.helpers.dicts import merge_dicts, dotdict
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                    '..', '..', 'src'))
    from yolapi.yola_configuration import merge_dicts, dotdict


def update_configuration(config):
    configuration = {
        'common': {
            'services': {
                'yolapi': {
                    'url': 'http://yolapi.localhost:8000',
                },
            },
        },
        'yolapi': {
            'deploy': {
                'enable_migrations': False,
                'install_path': '/srv/www/yolapi',
                'apache2': {
                    'build_config': True,
                    'vhost': 'yolapi.localhost',
                    'wsgi_webpath': '/',
                    'static_webpath': '/static',
                },
            },
            'application': {
                'url': 'http://yolapi.localhost:8000',
                'debug': False,
                'template_debug': False,
                'logfile_path': 'yolapi.log',
                'database':  {
                    'name': 'yolapi.sqlite',
                    'engine': 'sqlite3',
                    'user': '',
                    'password': '',
                    'host': '',
                    'port': '',
                },
            },
        },
    }
    config = merge_dicts(config, configuration)

if __name__ == '__main__':
    config = dotdict()
    update_configuration(config)
    with open('configuration.json', 'w') as f:
        f.write(json.dumps(config, indent=4))
