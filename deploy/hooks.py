from yola.deploy.hooks.django import DjangoApp
from yola.deploy.hooks.htpasswd import AuthenticatedApp


class Hooks(DjangoApp, AuthenticatedApp):
    migrate_on_deploy = True
    uses_south = True
    has_media = True
    has_static = True


hooks = Hooks
