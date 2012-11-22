import logging

from yola.deploy.hooks.django import DjangoApp
from yola.deploy.hooks.htpasswd import AuthenticatedApp
from yola.deploy.hooks.upstart import UpstartApp
from yola.deploy.util import touch

log = logging.getLogger(__name__)


class Hooks(DjangoApp, AuthenticatedApp, UpstartApp):
    migrate_on_deploy = True
    uses_south = True
    has_media = True
    has_static = True

    def prepare(self):
        super(Hooks, self).prepare()

        logfile = self.config.get(self.app).path.celery_log
        touch(logfile, 'www-data', 'adm', 0640)

hooks = Hooks
