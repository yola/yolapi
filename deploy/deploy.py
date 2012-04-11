"""
Application deploy script. This script is loaded by deploy. Thus imports, and
directories are all relative to that of deploy. As such, when doing something
like loading the log configuration this is really looking in
/Deploy/config/logging.conf is deploy has been installed at /Deploy.
Deploy is structured such that most of the code and magic tries to stay with
the deploy application, and the applications deploy handler just needs to
utilize the basic objects given to it, such as configuration, template objects,
etc...
"""

import datetime
import glob
import os
import shutil
from subprocess import check_call

# deploy libraries
from lib.helpers.filesystem import ensure_file, chown_tree, merge_tree
from lib.helpers.backup import backup as hbackup, restore_backup
from lib.helpers.templates import parse_template
from lib.helpers.django import install_virtual_env, management_command
from lib.common import log


def backup(config):
    '''
    backup the currently deployed version, and associated files
    This is mostly needed on env's where some dev's work in live code
    and sometimes they deploy by mistake.
    '''
    log.info('Backup application')
    tgz = os.path.join(config.deploy_settings.paths.backup,
                       'yolapi.%s.tar.gz'
                       % datetime.datetime.now().strftime('%Y-%m-%d.%H%M%S'))
    targets = [config.yolapi.deploy.install_path,
               config.yolapi.deploy.data_path]
    hbackup(targets, tgz)


def restore(config):
    '''
    restore the latest application backup, if anything earlier is wanted, the
    user must do it themselves.
    '''
    log.info('Restore latest application backup')
    options = glob.glob(os.path.join(config.deploy_settings.paths.backup,
                                     'yolapi.*.tar.gz'))
    options.sort()  # sorting string works for this date format
    tgz = options[-1]
    shutil.rmtree(config.yolapi.deploy.install_path)
    shutil.rmtree(config.yolapi.deploy.data_path)
    restore_backup(tgz)


def foundations(config):
    '''
    Prepare a workspace for distribution, preflight checks, etc...
    This is mostly a stub as the majority of work should have already been
    done by lib/workspaces.foundations.
    '''
    return


def preflight(config):
    '''
    verify the configuration, and the expected system state
    '''
    conf = config.yolapi

    if conf.deploy.install_path is None:
        raise Exception('Preflight failed, install_path has not been set')
    if conf.deploy.data_path is None:
        raise Exception('Preflight failed, data_path has not been set')


def prepare(config):
    '''
    config is the configuration object created by deploy by merging various
    configurations the cwd is the workspace directory for the application
    '''
    conf = config.yolapi
    gconf = config.common

    # For the SSL Vhost
    parse_template('apache2/ssl-vhost-snippet.conf.template',
                   './fs/etc/apache2/yola.d/yolapi',
                   conf=conf, gconf=gconf)

    # if we're building apache config
    if conf.deploy.apache2.build_config:
        parse_template('apache2/vhost.conf.template',
                       './fs/etc/apache2/sites-enabled/yolapi',
                       conf=conf, gconf=gconf)
        ensure_file('./fs/etc/apache2/sites-enabled/yolapi',
                    0644, 'root', 'root')

    # configure the wsgi handler
    parse_template('apache2/wsgi-handler.wsgi.template',
                   './fs/srv/www/yolapi.wsgi', conf=conf, gconf=gconf)
    ensure_file('./fs/srv/www/yolapi.wsgi', 0644, 'root', 'root')

    # copy the package into the fake fs
    target = './fs' + conf.deploy.install_path + '/yolapi'
    log.info('Copying application to the workspace temporary file structure: '
             '%s', target)
    if os.path.exists(target):
        log.warn('Target install directory exists, if this is not a recycled '
                 'workspace, verify your script. Removing.')
        shutil.rmtree(target)
    shutil.copytree('./src/yolapi', target)
    chown_tree(target, 'root', 'root')

    # copy the configuration json dump to the project home
    shutil.copy2('./configuration/configuration.json',
                 target + '/configuration.json')

    # install our virtual environment
    install_virtual_env('./fs/' + conf.deploy.install_path, './libs/')

    # Data area
    os.makedirs('./fs/' + conf.deploy.data_path)
    os.makedirs('./fs/' + os.path.join(conf.deploy.data_path,
                                       conf.application.dists_path))
    chown_tree('./fs/' + conf.deploy.data_path, 'www-data', 'www-data')


def migrate(config):
    '''
    run any database migrations needed
    '''
    conf = config.yolapi

    create = False
    if (conf.application.database.engine.endswith('sqlite3')
            and not os.path.isfile(conf.application.database.name)):
        create = True

    if create:
        # The database path is absolute, so this happens outside ./fs/
        os.makedirs(conf.deploy.data_path)

    if conf.deploy.enable_migrations or create:
        install_path = './fs' + config.yolapi.deploy.install_path
        management_command(install_path, 'yolapi', 'syncdb', '--noinput')
        management_command(install_path, 'yolapi', 'migrate', '--noinput')
        management_command(install_path, 'yolapi', 'loaddata',
                os.path.join(install_path, 'yolapi', 'initial_data.json'))
    else:
        log.info('Skipping migrations, they are disabled')

    if create:
        chown_tree(conf.deploy.data_path, 'www-data', 'www-data')


def deploy(config):
    # set up files outside of the ./fs, copy ./fs into place, restart services
    conf = config.yolapi

    # make sure the log file exists with the right permissions
    ensure_file(conf.application.logfile_path, 0644, 'www-data', 'www-data')

    # merge the virtual fs into /, essentially making it live
    # first remove the old install dir .../yolapi, we don't need to merge,
    # just put new dir
    if os.path.exists(conf.deploy.install_path):
        log.info('Deleting old application from %s', conf.deploy.install_path)
        shutil.rmtree(conf.deploy.install_path)
    merge_tree('./fs', '/')

    # TODO: This belongs elesewhere, but happens outside the fs, so...
    management_command(conf.deploy.install_path,
                       'yolapi', 'collectstatic', '--noinput')

    # graceful apache2
    log.info('Restarting apache (graceful)')
    try:
        check_call(('apache2ctl', 'graceful'))
    except:
        log.error('Failed to graceful apache, maybe apache is not installed')
