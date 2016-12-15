import os
import urllib
from datetime import timedelta

import djcelery
from django.template.loader import add_to_builtins
from kombu import Exchange, Queue
from yoconfigurator.base import read_config


app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',))
project_dir = os.path.realpath(os.path.join(app_dir, '..'))

conf = read_config(project_dir)
aconf = conf.yolapi
cconf = conf.common

DEBUG = aconf.debug
TEMPLATE_DEBUG = aconf.template_debug

ADMINS = (
    ('Yola Ops', 'ops@yola.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': aconf.db.engine,
        'NAME': aconf.db.name,
        'USER': aconf.db.user,
        'PASSWORD': aconf.db.password,
        'HOST': aconf.db.host,
        'PORT': aconf.db.port,
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(aconf.path.data, 'media') + '/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(project_dir, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '_pree(#lmyg74##*o#a@u2)@&su)f3j+8@cbe=+8ga2lj)d-@t'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

ROOT_URLCONF = 'yolapi.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'yolapi.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(app_dir, 'templates'),
)

INSTALLED_APPS = (
    'pypi',
    'importer',
    'sync',
    'eggbuilder',
    'crispy_forms',
    'django.contrib.staticfiles',
    'djcelery',
    'raven.contrib.django',
    'south',
    'django_nose',
)

RAVEN_CONFIG = {
    'dsn': aconf.sentry_dsn,
    'register_signals': True,
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'std': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': aconf.path.log,
            'formatter': 'std',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
    },
    'loggers': {
        'django.request': {
            'level': 'ERROR',
        },
        'raven': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'sentry.errors': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'yolapi': {
            'level': 'INFO',
        },
        'south': {
            'level': 'INFO',
        },
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry', 'logfile'],
    }
}

# Location of artifacts, within MEDIA_ROOT
PYPI_DISTS = 'dists'

# REMOTE_USERs who we will accept uploads from
PYPI_ALLOWED_UPLOADERS = aconf.allowed_uploaders

# Archive old artifacts on deletion/replacement?
# Set False disable
PYPI_ARCHIVE = 'archive'

# Allow overriding over existing packages
PYPI_ALLOW_REPLACEMENT = True

# Allow deleting packages
PYPI_ALLOW_DELETION = True

PYPI_ALLOWED_UPLOAD_TYPES = ('sdist',)

# An available formatting that can be used for displaying date fields on
# templates.
SHORT_DATE_FORMAT = 'Y-m-d'

# Always load future template tags
add_to_builtins('django.templatetags.future')

PYPI_SYNC_BUCKET = aconf.aws.archive_bucket
AWS_ACCESS_KEY = aconf.aws.access_key
AWS_SECRET_KEY = aconf.aws.secret_key

# Build eggs for
PYPI_EGG_PYVERSIONS = aconf.build_eggs_for

djcelery.setup_loader()
BROKER_URL = 'sqs://%s:%s@' % (
    urllib.quote(aconf.aws.access_key, ''),
    urllib.quote(aconf.aws.secret_key, ''),
)
BROKER_TRANSPORT_OPTIONS = {
    'polling_interval': 5.0,
    'queue_name_prefix': cconf.async_queue_prefix,
}
# We don't communicate with anybody else
CELERY_DEFAULT_QUEUE = 'yolapi-%s' % cconf.domain.hostname
CELERY_QUEUES = (
    Queue(CELERY_DEFAULT_QUEUE, Exchange('yolapi'), routing_key='yolapi.#'),
)

if PYPI_SYNC_BUCKET:
    CELERYBEAT_SCHEDULE = {
        'sync': {
            'task': 'yolapi.sync.tasks.sync',
            'schedule': timedelta(minutes=5),
        },
    }

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--with-specplugin', '--where=%s' % app_dir]
