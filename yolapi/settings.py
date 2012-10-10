import os
import urllib

from django.template.loader import add_to_builtins
from kombu import Exchange, Queue
import djcelery
from yola.configurator.base import read_config


app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
conf = read_config(app_dir)
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
STATIC_ROOT = os.path.join(app_dir, 'static')

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
    os.path.join(app_dir, 'yolapi', 'templates'),
)

INSTALLED_APPS = (
    'yolapi.pypi',
    'yolapi.importer',
    'yolapi.archive',

    'crispy_forms',
    'django.contrib.staticfiles',
    'djcelery',
    'raven.contrib.django',
    'south',
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
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry', 'logfile'],
    }
}

# Location of artifacts, within MEDIA_ROOT
PYPI_DISTS = 'dists'

# Archive old artifacts on deletion/replacement?
# Set False disable
PYPI_ARCHIVE = 'archive'

# Allow overriding over existing packages
PYPI_ALLOW_REPLACEMENT = True

# An available formatting that can be used for displaying date fields on
# templates.
SHORT_DATE_FORMAT = 'Y-m-d'

# Always load future template tags
add_to_builtins('django.templatetags.future')

YOLAPI_ARCHIVE_BUCKET = aconf.aws.archive_bucket
AWS_ACCESS_KEY = aconf.aws.accesskey
AWS_SECRET_KEY = aconf.aws.secretkey

djcelery.setup_loader()
BROKER_URL = 'sqs://%s:%s@' % (
    urllib.quote(aconf.aws.accesskey, ''),
    urllib.quote(aconf.aws.secretkey, ''),
)
BROKER_TRANSPORT_OPTIONS = {
    'polling_interval': 5.0,
    'queue_name_prefix': cconf.async_queue_prefix,
}
CELERY_DEFAULT_QUEUE = 'yolapi'
CELERY_QUEUES = (
    Queue('yolapi', Exchange('yolapi'), routing_key='yolapi.#'),
)
