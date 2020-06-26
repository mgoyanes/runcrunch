from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .scripts import webhook_event

import json

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def event(request):

    try: # Handle main incoming webhook events
        body = json.loads(request.body)
        print('EVENT:', body)

        if body['aspect_type'] == 'create' and body['object_type'] == 'activity':
            webhook_event.new_activity(int(body['owner_id']), int(body['object_id']))
        elif body['aspect_type'] == 'update' and body['object_type'] == 'activity' and 'title' in body['updates'].keys():
            webhook_event.update_title(int(body['object_id']), body['updates']['title'])
        elif body['aspect_type'] == 'delete' and body['object_type'] == 'activity':
            webhook_event.delete_activity(int(body['object_id']))
        elif body['aspect_type'] == 'update' and body['object_type'] == 'athlete' and body['updates']['authorized'] == 'false':
            webhook_event.deauthorize(int(body['owner_id']))
    except: # Handle webhook subscription creation
        try:
            print('SUBSCRIPTION:', dict(request.GET.items()))
            challenge = dict(request.GET.items())['hub.challenge']
            response = JsonResponse({"hub.challenge": challenge})
            return HttpResponse(response, status=200)
        except:
            return HttpResponse(status=500)

    return HttpResponse(status=200)