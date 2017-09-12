import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yolapi.settings')

from celery import Celery  # NOQA
from django.conf import settings  # NOQA

broker_url = 'redis://{host}:{port}/{db}'.format(**settings.REDIS)

app = Celery('yolapi', broker=broker_url)

app.conf.update(
    task_default_queue=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_default_routing_key='yolapi.#',
    task_ignore_result=True,
)

if settings.PYPI_SYNC_BUCKET:
    app.conf.update(
        beat_schedule={
            'sync': {
                'task': 'sync.tasks.sync',
                'schedule': 5 * 60,  # 5 minutes
            },
        }
    )

app.autodiscover_tasks()
