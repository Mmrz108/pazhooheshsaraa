import logging

from django.conf import settings

from apps.users.services.bale import BaleError, send_bale_otp
from apps.users.services.sms import SMSError, send_otp_sms

logger = logging.getLogger(__name__)


class OTPDeliveryError(Exception):
    def __init__(self, message, code='otp_delivery_error'):
        self.message = message
        self.code = code
        super().__init__(message)


def send_otp_code(mobile: str, code: str) -> dict:
    """
    Send OTP via Kavenegar Verify Lookup and Bale app.
    At least one channel must succeed.
    """
    delivered = []
    errors = []

    try:
        send_otp_sms(mobile, code)
        delivered.append('sms')
    except SMSError as exc:
        errors.append(f'SMS: {exc.message}')
        logger.error('SMS OTP failed for %s: %s', mobile, exc.message)

    if settings.BALE_ENABLED:
        try:
            if send_bale_otp(mobile, code):
                delivered.append('bale')
        except BaleError as exc:
            if exc.code == 'not_bale_user':
                logger.info('Bale OTP skipped for %s: user has no Bale account.', mobile)
            else:
                errors.append(f'Bale: {exc.message}')
                logger.warning('Bale OTP failed for %s: %s', mobile, exc.message)

    if not delivered:
        message = 'امکان ارسال کد تأیید وجود ندارد. لطفاً بعداً تلاش کنید.'
        if errors:
            message = errors[0].split(': ', 1)[-1]
        raise OTPDeliveryError(message, code='delivery_failed')

    return {'channels': delivered, 'errors': errors}

