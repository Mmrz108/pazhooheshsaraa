import json
import logging
import random
import re
import string
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache

from common.validators import normalize_digits, normalize_mobile, validate_iranian_mobile, validate_iranian_national_code

User = get_user_model()
logger = logging.getLogger(__name__)


class OTPError(Exception):
    def __init__(self, message, code='otp_error'):
        self.message = message
        self.code = code
        super().__init__(message)


class OTPService:
    OTP_PREFIX = 'otp:auth:'
    RATE_PREFIX = 'otp:rate:'
    SEND_COUNT_PREFIX = 'otp:send_count:'
    VERIFIED_PREFIX = 'otp:verified:'
    REGISTRATION_TTL = 600

    def __init__(self):
        self.expiry = settings.OTP_EXPIRY_SECONDS
        self.max_attempts = settings.OTP_MAX_ATTEMPTS
        self.resend_cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS
        self.max_sends_per_hour = settings.OTP_MAX_SENDS_PER_HOUR

    def _otp_key(self, mobile: str) -> str:
        return f'{self.OTP_PREFIX}{mobile}'

    def _rate_key(self, mobile: str) -> str:
        return f'{self.RATE_PREFIX}{mobile}'

    def _send_count_key(self, mobile: str) -> str:
        return f'{self.SEND_COUNT_PREFIX}{mobile}'

    def _verified_key(self, mobile: str) -> str:
        return f'{self.VERIFIED_PREFIX}{mobile}'

    def _generate_code(self) -> str:
        return ''.join(random.choices(string.digits, k=6))

    def _normalize_code(self, code: str) -> str:
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        normalized = str(code).strip()
        for index, digit in enumerate(persian_digits):
            normalized = normalized.replace(digit, str(index))
        normalized = re.sub(r'\D', '', normalized)
        return normalized

    def _get_resend_cooldown(self, mobile: str) -> int:
        expires_at = cache.get(self._rate_key(mobile))
        if not expires_at:
            return 0
        return max(0, int(expires_at) - int(time.time()))

    def _check_rate_limits(self, mobile: str, is_resend: bool = False):
        if is_resend:
            cooldown = self._get_resend_cooldown(mobile)
            if cooldown > 0:
                raise OTPError(
                    f'لطفاً {cooldown} ثانیه دیگر تلاش کنید.',
                    code='resend_cooldown',
                )

        send_count = cache.get(self._send_count_key(mobile)) or 0
        if int(send_count) >= self.max_sends_per_hour:
            raise OTPError(
                'تعداد درخواست‌های OTP بیش از حد مجاز است. یک ساعت دیگر تلاش کنید.',
                code='rate_limit_exceeded',
            )

    def send_otp(self, mobile: str) -> dict:
        mobile = normalize_mobile(mobile)
        validate_iranian_mobile(mobile)

        existing = cache.get(self._otp_key(mobile))
        is_resend = existing is not None
        self._check_rate_limits(mobile, is_resend=is_resend)

        code = self._generate_code()
        data = {
            'code': code,
            'mobile': mobile,
            'attempts': 0,
            'is_existing_user': User.objects.filter(mobile=mobile).exists(),
        }

        cache.set(self._otp_key(mobile), json.dumps(data), timeout=self.expiry)
        cache.set(
            self._rate_key(mobile),
            int(time.time()) + self.resend_cooldown,
            timeout=self.resend_cooldown,
        )

        send_count = cache.get(self._send_count_key(mobile)) or 0
        cache.set(self._send_count_key(mobile), int(send_count) + 1, timeout=3600)

        from apps.users.services.otp_delivery import OTPDeliveryError, send_otp_code

        result = {
            'mobile': mobile,
            'expires_in': self.expiry,
            'resend_cooldown': self.resend_cooldown,
            'is_existing_user': data['is_existing_user'],
            'message': 'کد تأیید ارسال شد.',
        }

        if settings.OTP_DEBUG_VISIBLE:
            result['debug_otp'] = code
            logger.warning('[OTP DEBUG] mobile=%s code=%s', mobile, code)

        try:
            send_otp_code(mobile, code)
        except OTPDeliveryError as exc:
            if settings.OTP_DEBUG_VISIBLE:
                result['message'] = (
                    'ارسال پیامک/بله ناموفق بود. کد تست در صفحه نمایش داده شد.'
                )
                return result
            raise OTPError(exc.message, code=exc.code) from exc

        return result

    def resend_otp(self, mobile: str) -> dict:
        mobile = normalize_mobile(mobile)
        if not cache.get(self._otp_key(mobile)):
            raise OTPError(
                'درخواست یافت نشد. لطفاً مجدداً شماره موبایل را وارد کنید.',
                code='not_found',
            )
        return self.send_otp(mobile)

    def verify_otp(self, mobile: str, code: str) -> dict:
        mobile = normalize_mobile(mobile)
        raw = cache.get(self._otp_key(mobile))
        if not raw:
            raise OTPError(
                'کد تأیید منقضی شده است. لطفاً مجدداً درخواست دهید.',
                code='expired',
            )

        data = json.loads(raw)
        data['attempts'] = data.get('attempts', 0) + 1

        if data['attempts'] > self.max_attempts:
            cache.delete(self._otp_key(mobile))
            raise OTPError(
                'تعداد تلاش‌های ناموفق بیش از حد مجاز است.',
                code='max_attempts',
            )

        if self._normalize_code(data['code']) != self._normalize_code(code):
            cache.set(self._otp_key(mobile), json.dumps(data), timeout=self.expiry)
            raise OTPError('کد تأیید نادرست است.', code='invalid_code')

        cache.delete(self._otp_key(mobile))

        user = User.objects.filter(mobile=mobile).first()
        if user:
            if not user.is_active:
                raise OTPError('حساب کاربری غیرفعال است.', code='inactive_user')
            return {'action': 'login', 'user': user}

        cache.set(self._verified_key(mobile), True, timeout=self.REGISTRATION_TTL)
        return {'action': 'register', 'mobile': mobile}

    def complete_registration(
        self,
        mobile: str,
        first_name: str,
        last_name: str,
        national_code: str,
        father_name: str,
        birth_date,
    ) -> User:
        mobile = normalize_mobile(mobile)
        validate_iranian_mobile(mobile)
        national_code = normalize_digits(national_code)
        validate_iranian_national_code(national_code)

        if not cache.get(self._verified_key(mobile)):
            raise OTPError(
                'ابتدا کد تأیید را وارد کنید یا مجدداً درخواست دهید.',
                code='not_verified',
            )

        if User.objects.filter(mobile=mobile).exists():
            cache.delete(self._verified_key(mobile))
            raise OTPError('این شماره موبایل قبلاً ثبت شده است.', code='mobile_exists')

        if User.objects.filter(national_code=national_code).exists():
            raise OTPError('این کد ملی قبلاً ثبت شده است.', code='national_code_exists')

        user = User.objects.create_user(
            mobile=mobile,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            national_code=national_code,
            father_name=father_name.strip(),
            birth_date=birth_date,
        )
        cache.delete(self._verified_key(mobile))
        return user
