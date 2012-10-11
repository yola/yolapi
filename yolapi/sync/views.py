from django.views.decorators.http import require_POST
from django.http import HttpResponse

import yolapi.sync.tasks


@require_POST
def sync(request):
    yolapi.sync.tasks.sync.delay()
    return HttpResponse('Sync Queued', content_type='text/plain')
