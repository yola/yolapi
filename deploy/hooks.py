import logging

from yodeploy.hooks.data import DataDirApp
from yodeploy.hooks.django import DjangoApp
from yodeploy.hooks.htpasswd import AuthenticatedApp
from yodeploy.hooks.upstart import UpstartApp
from yodeploy.util import touch

log = logging.getLogger(__name__)


class Hooks(DjangoApp, AuthenticatedApp, UpstartApp, DataDirApp):
    migrate_on_deploy = False
    has_static = True

    def prepare(self):
        super(Hooks, self).prepare()

        logfile = self.config.get(self.app).path.celery_log
        touch(logfile, 'www-data', 'adm', 0640)

hooks = Hooks
