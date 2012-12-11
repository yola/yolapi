from yola.configurator.dicts import merge_dicts


def update(config):
    fqdn = config.common.domain.fqdn
    new = {
        'yolapi': {
            'ssl': {
                'cert': '/etc/ssl/certs/%s.pem' % fqdn,
                'key': '/etc/ssl/private/%s.key' % fqdn,
            },
        },
    }
    return merge_dicts(config, new)
