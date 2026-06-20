import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

KAVENEGAR_ERROR_MESSAGES = {
    401: 'کلید API کاوه‌نگار نامعتبر است.',
    402: 'اعتبار حساب کاوه‌نگار کافی نیست.',
    403: 'دسترسی به این سرویس مجاز نیست.',
    418: 'اعتبار حساب کاوه‌نگار کافی نیست.',
    422: 'داده‌های ارسالی نامعتبر است.',
    424: 'الگوی OTP یافت نشد یا هنوز در پنل کاوه‌نگار تأیید نشده است.',
    426: 'این سرویس نیازمند فعال‌سازی سرویس پیشرفته در کاوه‌نگار است.',
    427: 'استفاده از این خط نیازمند ایجاد سطح دسترسی در پنل کاوه‌نگار است.',
    430: 'حساب کاوه‌نگار احراز هویت نشده است. از پنل kavenegar.com احراز هویت را تکمیل کنید.',
    431: 'سرویس پیامک برای این حساب فعال نیست.',
    432: 'پارامتر %token در الگوی OTP تعریف نشده است.',
}


class SMSError(Exception):
    def __init__(self, message, code='sms_error'):
        self.message = message
        self.code = code
        super().__init__(message)


def send_otp_sms(mobile: str, code: str) -> bool:
    """Send OTP via Kavenegar Verify Lookup (recommended for login/register)."""
    provider = settings.SMS_PROVIDER

    if provider == 'console':
        logger.info('[SMS OTP -> %s] %s', mobile, code)
        return True

    if provider == 'kavenegar':
        return _send_via_kavenegar_lookup(mobile, code)

    return send_sms(mobile, f'کد تأیید پژوهشسرا: {code}')


def send_sms(mobile: str, message: str) -> bool:
    """Send SMS via configured provider."""
    provider = settings.SMS_PROVIDER

    if provider == 'console':
        logger.info('[SMS -> %s] %s', mobile, message)
        return True

    if provider == 'kavenegar':
        return _send_via_kavenegar(mobile, message)

    logger.warning('SMS provider "%s" not implemented. Message logged only.', provider)
    logger.info('[SMS -> %s] %s', mobile, message)
    return True


def _parse_kavenegar_error(exc) -> tuple[int | None, str]:
    raw = exc.args[0] if exc.args else ''
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')
    else:
        raw = str(raw)
    match = re.search(r'APIException\[(\d+)\]\s*(.*)', raw, re.DOTALL)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None, raw


def _get_kavenegar_api():
    api_key = settings.SMS_API_KEY
    if not api_key:
        raise SMSError('کلید API پیامک تنظیم نشده است.', code='missing_api_key')

    try:
        from kavenegar import KavenegarAPI
    except ImportError as exc:
        raise SMSError('پکیج kavenegar نصب نشده است.', code='missing_package') from exc

    return KavenegarAPI(api_key)


def _handle_kavenegar_exception(exc, mobile: str, fallback_label: str) -> bool:
    from kavenegar import APIException, HTTPException

    if isinstance(exc, APIException):
        status_code, provider_msg = _parse_kavenegar_error(exc)
        logger.error(
            'Kavenegar API error [%s] for %s: %s',
            status_code, mobile, provider_msg,
        )
        if settings.SMS_FALLBACK_CONSOLE:
            logger.warning('[SMS FALLBACK -> %s] %s', mobile, fallback_label)
            return True
        user_message = KAVENEGAR_ERROR_MESSAGES.get(
            status_code,
            'خطا در ارسال پیامک. لطفاً بعداً تلاش کنید.',
        )
        raise SMSError(user_message, code=f'kavenegar_{status_code or "api"}') from exc

    if isinstance(exc, HTTPException):
        logger.error('Kavenegar HTTP error for %s: %s', mobile, exc)
        if settings.SMS_FALLBACK_CONSOLE:
            logger.warning('[SMS FALLBACK -> %s] %s', mobile, fallback_label)
            return True
        raise SMSError('خطا در اتصال به سرویس پیامک.', code='kavenegar_http') from exc

    raise exc


def _send_via_kavenegar_lookup(mobile: str, code: str) -> bool:
    template = getattr(settings, 'KAVENEGAR_OTP_TEMPLATE', '') or 'pazhooheshsara-otp'
    token = re.sub(r'\D', '', str(code))
    if len(token) != 6:
        raise SMSError('کد OTP باید ۶ رقم باشد.', code='invalid_otp')

    params = {
        'receptor': mobile,
        'token': token,
        'template': template,
        'type': 'sms',
    }

    try:
        from kavenegar import APIException, HTTPException

        api = _get_kavenegar_api()
        response = api.verify_lookup(params)
        logger.info('Kavenegar OTP lookup sent to %s via template %s: %s', mobile, template, response)
        return True
    except (APIException, HTTPException) as exc:
        return _handle_kavenegar_exception(exc, mobile, f'OTP code={token}')
    except Exception as exc:
        logger.error('Kavenegar OTP lookup error for %s: %s', mobile, exc)
        if settings.SMS_FALLBACK_CONSOLE:
            logger.warning('[SMS FALLBACK -> %s] OTP code=%s', mobile, token)
            return True
        raise SMSError('خطا در ارسال کد تأیید.', code='kavenegar_lookup') from exc


def _send_via_kavenegar(mobile: str, message: str) -> bool:
    sender = settings.SMS_SENDER

    if not sender:
        raise SMSError('شماره خط ارسال پیامک تنظیم نشده است.', code='missing_sender')

    params = {
        'sender': sender,
        'receptor': mobile,
        'message': message,
    }

    try:
        from kavenegar import APIException, HTTPException

        api = _get_kavenegar_api()
        response = api.sms_send(params)
        logger.info('Kavenegar SMS sent to %s: %s', mobile, response)
        return True
    except (APIException, HTTPException) as exc:
        return _handle_kavenegar_exception(exc, mobile, message)
