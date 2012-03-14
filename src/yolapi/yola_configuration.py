import os
import sys

try:
    import json
except ImportError:
    import simplejson as json


class dotdict(dict):
    '''
    this is a cleaner way to read a dict in the templates
    instead of using dict['field'], can now use dict.field
    '''
    def __getattr__(self, attr):
        obj = self.get(attr, None)
        if isinstance(obj, dict):
            return dotdict(obj)
        else:
            return obj
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def iteritems(self):
        for k, v in dict.iteritems(self):
            if isinstance(v, dict):
                yield (k, dotdict(v))
            else:
                yield (k, v)


def merge_dicts(d1, d2):
    '''
    merge dictionary d2 into d1, used to compile application settings
    d2 will override settings in d1. d2 can be thought of as the information
    that will be added to d1 (and overriding d1).
    '''
    if isinstance(d1, dict) and isinstance(d2, dict):
        for k, v in d2.iteritems():
            if k not in d1:
                d1[k] = v
            else:
                if isinstance(v, dict):
                    d1[k] = merge_dicts(d1[k], v)
                else:
                    # override value
                    d1[k] = v
    return d1


def load_configuration(cname):
    conf = []
    for pypath in sys.path:
        possible_target = os.path.join(pypath, cname)
        if os.path.exists(possible_target):
            with open(possible_target) as f:
                conf.append(dotdict(json.loads(f.read())))

    if len(conf) > 1:
        raise Exception('Multiple configurations found.')
    elif conf:
        return conf[0]
    else:
        raise Exception('Configuration not found, searched python path for '
                        'configuration.json')
