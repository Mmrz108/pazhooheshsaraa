import logging
import uuid

import requests
from django.conf import settings
from django.core.cache import cache

from common.validators import normalize_mobile

logger = logging.getLogger(__name__)

BALE_GATEWAY_TOKEN_CACHE_KEY = 'bale:gateway:access_token'

BALE_ERROR_MESSAGES = {
    2: 'خطای داخلی سرویس بله.',
    3: 'محدودیت ارسال پیام در بله.',
    4: 'درخواست نامعتبر برای سرویس بله.',
    8: 'شماره موبایل برای بله نامعتبر است.',
    17: 'این شماره در اپلیکیشن بله ثبت نشده است.',
    18: 'محدودیت ارسال OTP در بله.',
    20: 'اعتبار سرویس بله کافی نیست.',
    21: 'محدودیت مخاطبین بازوی بله.',
}


class BaleError(Exception):
    def __init__(self, message, code='bale_error', status_code=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def to_bale_phone(mobile: str) -> str:
    """Convert 09xxxxxxxxx to 989xxxxxxxxx for Bale APIs."""
    mobile = normalize_mobile(mobile)
    if mobile.startswith('0'):
        return f'98{mobile[1:]}'
    if mobile.startswith('98'):
        return mobile
    if mobile.startswith('9') and len(mobile) == 10:
        return f'98{mobile}'
    return mobile


def verify_bot_token() -> bool:
    token = settings.BALE_BOT_TOKEN
    if not token:
        return False
    try:
        response = requests.get(
            f'https://tapi.bale.ai/bot{token}/getMe',
            timeout=10,
        )
        data = response.json()
        if data.get('ok'):
            logger.info(
                'Bale bot connected: @%s (id=%s)',
                data['result'].get('username'),
                data['result'].get('id'),
            )
            return True
    except requests.RequestException as exc:
        logger.error('Bale bot getMe failed: %s', exc)
    return False


def _parse_safir_errors(data: dict, mobile: str):
    error_data = data.get('error_data') or []
    if not error_data:
        return
    first_error = error_data[0]
    error_code = first_error.get('code')
    description = first_error.get('description') or BALE_ERROR_MESSAGES.get(
        error_code,
        'خطا در ارسال OTP از طریق بله.',
    )
    logger.warning('Bale Safir error [%s] for %s: %s', error_code, mobile, description)
    if error_code == 17:
        raise BaleError(description, code='not_bale_user', status_code=error_code)
    raise BaleError(description, code=f'bale_{error_code}', status_code=error_code)


def _send_via_safir_v3(mobile: str, otp_code: str) -> bool:
    api_key = settings.BALE_API_ACCESS_KEY
    bot_id = settings.BALE_BOT_ID
    if not api_key:
        return False

    phone_number = to_bale_phone(mobile)
    payload = {
        'request_id': str(uuid.uuid4()),
        'bot_id': int(bot_id),
        'phone_number': phone_number,
        'message_data': {
            'otp_message': {
                'otp': str(otp_code),
            },
        },
    }
    response = requests.post(
        settings.BALE_API_URL,
        json=payload,
        headers={
            'api-access-key': api_key,
            'Content-Type': 'application/json',
        },
        timeout=15,
    )
    if response.status_code >= 500:
        raise BaleError('سرویس بله در دسترس نیست.', code='bale_server')

    data = response.json()
    _parse_safir_errors(data, mobile)

    if response.status_code >= 400:
        raise BaleError('خطا در ارسال OTP از طریق سفیر بله.', code='bale_api')

    logger.info('Bale Safir v3 OTP sent to %s: message_id=%s', mobile, data.get('message_id'))
    return True


def _get_gateway_access_token() -> str:
    cached = cache.get(BALE_GATEWAY_TOKEN_CACHE_KEY)
    if cached:
        return cached

    client_id = settings.BALE_CLIENT_ID
    client_secret = settings.BALE_CLIENT_SECRET
    response = requests.post(
        settings.BALE_GATEWAY_TOKEN_URL,
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'read',
        },
        timeout=15,
    )
    if response.status_code != 200:
        logger.error('Bale gateway auth failed: %s', response.text)
        raise BaleError('احراز هویت درگاه OTP بله ناموفق بود.', code='bale_auth')

    data = response.json()
    token = data['access_token']
    expires_in = int(data.get('expires_in', 43200))
    cache.set(BALE_GATEWAY_TOKEN_CACHE_KEY, token, timeout=max(expires_in - 120, 60))
    return token


def _send_via_gateway_v2(mobile: str, otp_code: str) -> bool:
    if not settings.BALE_CLIENT_ID or not settings.BALE_CLIENT_SECRET:
        return False

    token = _get_gateway_access_token()
    phone_number = to_bale_phone(mobile)
    response = requests.post(
        settings.BALE_GATEWAY_OTP_URL,
        json={
            'phone': phone_number,
            'otp': int(otp_code),
        },
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        timeout=15,
    )

    if response.status_code == 404:
        data = response.json()
        if data.get('code') == 17:
            raise BaleError(
                BALE_ERROR_MESSAGES[17],
                code='not_bale_user',
                status_code=17,
            )

    if response.status_code == 402:
        raise BaleError(BALE_ERROR_MESSAGES[20], code='bale_payment', status_code=20)

    if response.status_code == 429 or response.status_code == 400:
        try:
            data = response.json()
            code = data.get('code')
            if code == 18:
                raise BaleError(BALE_ERROR_MESSAGES[18], code='bale_rate_limit', status_code=18)
            if code == 17:
                raise BaleError(BALE_ERROR_MESSAGES[17], code='not_bale_user', status_code=17)
        except ValueError:
            pass

    if response.status_code >= 400:
        logger.error('Bale gateway OTP failed for %s: %s', mobile, response.text)
        raise BaleError('خطا در ارسال OTP از طریق درگاه بله.', code='bale_gateway')

    data = response.json()
    logger.info('Bale gateway v2 OTP sent to %s, balance=%s', mobile, data.get('balance'))
    return True


def send_bale_otp(mobile: str, otp_code: str) -> bool:
    """Send OTP via Bale (Safir v3 or Gateway v2)."""
    if not settings.BALE_ENABLED:
        return False

    if not settings.BALE_BOT_ID:
        logger.warning('Bale OTP skipped: BALE_BOT_ID not configured.')
        return False

    has_safir = bool(settings.BALE_API_ACCESS_KEY)
    has_gateway = bool(settings.BALE_CLIENT_ID and settings.BALE_CLIENT_SECRET)

    if not has_safir and not has_gateway:
        if settings.BALE_BOT_TOKEN:
            verify_bot_token()
        logger.warning(
            'Bale OTP skipped: set BALE_API_ACCESS_KEY (Safir) or '
            'BALE_CLIENT_ID/BALE_CLIENT_SECRET (Gateway) in .env. '
            'Bot token alone cannot send OTP by phone number.',
        )
        return False

    try:
        if has_safir and _send_via_safir_v3(mobile, otp_code):
            return True
    except BaleError:
        raise
    except requests.RequestException as exc:
        logger.error('Bale Safir request failed for %s: %s', mobile, exc)
        if not has_gateway:
            raise BaleError('خطا در اتصال به سرویس بله.', code='bale_http') from exc

    if has_gateway:
        return _send_via_gateway_v2(mobile, otp_code)

    return False
