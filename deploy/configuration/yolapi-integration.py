import socket

from yola.configurator.dicts import merge_dicts


def update(config):
    new = {
        'yolapi': {
            'domain': 'yolapi.%s' % socket.getfqdn(),
        },
    }
    return merge_dicts(config, new)
