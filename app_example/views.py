from django.http import JsonResponse
from app_example.tasks import send_notification_task


# An example view calling a celery task
def notify(request):
    send_notification_task.delay("hello celery task")
    return JsonResponse({"status": "OK"})
