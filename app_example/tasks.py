from celery import shared_task

from app_example.services.notifcation_service import send_notification


# An example task
@shared_task
def send_notification_task(content: str):
    send_notification(content=content)
