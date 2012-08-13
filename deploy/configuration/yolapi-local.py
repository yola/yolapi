from yola.configurator.dicts import merge_dicts


def update(config):
    new = {
        'yolapi': {
            'debug': True,
            'template_debug': True,
            'path': {
                'data': './data',
                'log': './data/yolapi.log',
            },
            'db':  {
                'name': './data/yolapi.sqlite',
            },
        },
    }
    return merge_dicts(config, new)
