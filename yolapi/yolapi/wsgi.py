import os
import sys


# mod_wsgi's base python installation is contaminated with package
# installations. The following code removes the impacted paths of the
# contaminated python installation so that yolapi (and its virtualenv)
# can run in isolation. This code will be unnecessary once Apache can be
# globally configured to point at an empty virtualenv with WSGIPythonHome.
def bad_path(path):
    version = "%d.%d" % sys.version_info[0:2]
    return (path.startswith('/usr/lib/python%s/dist-packages' % version) or
            path.startswith('/usr/lib/pymodules/python%s' % version))


sys.path = [path for path in sys.path if not bad_path(path)]

# The following line must come before django related imports or django will be
# unable to locate a settings module.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yolapi.settings")


from django.core.wsgi import get_wsgi_application  # NOQA
from raven.contrib.django.middleware.wsgi import Sentry  # NOQA

application = Sentry(get_wsgi_application())
