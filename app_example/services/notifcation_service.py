import logging

logger = logging.getLogger(__name__)

# An example of a service that celery can call
def send_notification(content: str):
    logger.info(f"Sending notification: {content}")
    return True