from celery import shared_task

from apps.users.services.sms import send_sms


@shared_task
def send_sms_task(mobile: str, message: str) -> bool:
    return send_sms(mobile, message)
