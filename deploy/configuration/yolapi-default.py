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
        'yolapi': {
            'deploy': {
                'enable_migrations': False,
                'install_path': '/srv/www/yolapi',
                'apache2': {
                    'build_config': True,
                    'wsgi_webpath': '/',
                    'static_webpath': '/static',
                },
            },
            'application': {
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
    config = dotdict({
        'common': {
            'services': {
                'yolapi': {
                    'domain': 'yolapi.localhost',
                    'url': 'http://yolapi.localhost:8000',
                },
            },
        },
    })
    update_configuration(config)
    with open('configuration.json', 'w') as f:
        f.write(json.dumps(config, indent=4))
