from yola.configurator.dicts import merge_dicts


def update(config):
    new = {
        'yolapi': {
            'ssl': {
                'cert': '/etc/apache2/certs/wildcard.qa.yola.net.crt',
                'key': '/etc/apache2/certs/wildcard.qa.yola.net.key',
            },
        },
    }
    return merge_dicts(config, new)
