from yola.configurator.dicts import merge_dicts


def update(config):
    hostname = config.common.domain.hostname
    new = {
        'yolapi': {
            'ssl': {
                'cert': '/etc/ssl/certs/%s.pem' % hostname,
                'key': '/etc/ssl/private/%s.key' % hostname,
            },
        },
    }
    return merge_dicts(config, new)
