import logging

from yodeploy.hooks.daemon import DaemonApp
from yodeploy.hooks.data import DataDirApp
from yodeploy.hooks.django import DjangoApp
from yodeploy.hooks.htpasswd import AuthenticatedApp

log = logging.getLogger(__name__)


class Hooks(DjangoApp, AuthenticatedApp, DaemonApp, DataDirApp):
    migrate_on_deploy = True
    has_static = True

hooks = Hooks
