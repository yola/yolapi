import logging
import subprocess

from yola.deploy.hooks.django import DjangoApp
from yola.deploy.hooks.htpasswd import AuthenticatedApp
from yola.deploy.util import touch

log = logging.getLogger(__name__)


class Hooks(DjangoApp, AuthenticatedApp):
    migrate_on_deploy = True
    uses_south = True
    has_media = True
    has_static = True

    def deployed(self):
        super(Hooks, self).deployed()
        # rankmonitor worker upstart
        self.template('upstart/celery.template',
                      '/etc/init/yolapi-worker.conf')

        logfile = self.config.get(self.app).path.celery_log
        touch(logfile, 'www-data', 'adm', 0640)

        try:
            subprocess.call(('service', 'yolapi-worker', 'stop'))
            subprocess.check_call(('service', 'yolapi-worker', 'start'))
        except subprocess.CalledProcessError:
            log.error('Unable to restart worker')

hooks = Hooks
