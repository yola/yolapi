from yola.deploy.hooks.django import DjangoApp


class Hooks(DjangoApp):
    migrate_on_deploy = True
    uses_south = True


hooks = Hooks
