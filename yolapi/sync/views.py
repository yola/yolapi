from django.http import HttpResponse
from django.views.decorators.http import require_POST

from sync import tasks


@require_POST
def sync(request):
    tasks.sync.delay()
    return HttpResponse('Sync Queued', content_type='text/plain')
