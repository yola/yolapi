import logging

from yodeploy.hooks.daemon import DaemonApp
from yodeploy.hooks.data import DataDirApp
from yodeploy.hooks.django import ApacheHostedDjangoApp
from yodeploy.hooks.htpasswd import AuthenticatedApp
from yodeploy.util import touch

log = logging.getLogger(__name__)


class Hooks(ApacheHostedDjangoApp, AuthenticatedApp, DaemonApp, DataDirApp):
    migrate_on_deploy = True
    has_static = True

    def prepare(self):
        super(Hooks, self).prepare()
        touch(
            self.config['yolapi'].path.uwsgi_log,
            self.log_user,
            self.log_group,
            0o640,
        )

    def apache_hosted_prepare(self):
        super(Hooks, self).apache_hosted_prepare()
        self.template(
            'uwsgi/yolapi.ini.template',
            '/etc/uwsgi/yolapi.ini'
        )


hooks = Hooks
