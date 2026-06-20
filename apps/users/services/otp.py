import logging
import random
import re
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users.models import OTPChallenge
from common.validators import normalize_digits, normalize_mobile, validate_iranian_mobile, validate_iranian_national_code

User = get_user_model()
logger = logging.getLogger(__name__)


class OTPError(Exception):
    def __init__(self, message, code='otp_error'):
        self.message = message
        self.code = code
        super().__init__(message)


class OTPService:
    REGISTRATION_TTL = 600

    def __init__(self):
        self.expiry = settings.OTP_EXPIRY_SECONDS
        self.max_attempts = settings.OTP_MAX_ATTEMPTS
        self.resend_cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS
        self.max_sends_per_hour = settings.OTP_MAX_SENDS_PER_HOUR

    def _generate_code(self) -> str:
        return ''.join(random.choices(string.digits, k=6))

    def _normalize_code(self, code: str) -> str:
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        normalized = str(code).strip()
        for index, digit in enumerate(persian_digits):
            normalized = normalized.replace(digit, str(index))
        normalized = re.sub(r'\D', '', normalized)
        return normalized

    def _get_challenge(self, mobile: str) -> OTPChallenge | None:
        return OTPChallenge.objects.filter(mobile=mobile).first()

    def _get_resend_cooldown(self, mobile: str) -> int:
        challenge = self._get_challenge(mobile)
        if not challenge or not challenge.last_sent_at:
            return 0
        remaining = int((challenge.last_sent_at + timezone.timedelta(seconds=self.resend_cooldown) - timezone.now()).total_seconds())
        return max(0, remaining)

    def _check_rate_limits(self, mobile: str, challenge: OTPChallenge | None, is_resend: bool = False):
        if is_resend:
            cooldown = self._get_resend_cooldown(mobile)
            if cooldown > 0:
                raise OTPError(
                    f'لطفاً {cooldown} ثانیه دیگر تلاش کنید.',
                    code='resend_cooldown',
                )

        if not challenge:
            return

        window_age = timezone.now() - challenge.send_window_started
        if window_age.total_seconds() < 3600 and challenge.send_count >= self.max_sends_per_hour:
            raise OTPError(
                'تعداد درخواست‌های OTP بیش از حد مجاز است. یک ساعت دیگر تلاش کنید.',
                code='rate_limit_exceeded',
            )

    def send_otp(self, mobile: str) -> dict:
        mobile = normalize_mobile(mobile)
        validate_iranian_mobile(mobile)

        challenge = self._get_challenge(mobile)
        is_resend = challenge is not None and not challenge.is_verified
        self._check_rate_limits(mobile, challenge, is_resend=is_resend)

        code = self._generate_code()
        now = timezone.now()
        expires_at = now + timezone.timedelta(seconds=self.expiry)

        if challenge and (now - challenge.send_window_started).total_seconds() >= 3600:
            send_count = 1
            send_window_started = now
        elif challenge:
            send_count = challenge.send_count + 1
            send_window_started = challenge.send_window_started
        else:
            send_count = 1
            send_window_started = now

        OTPChallenge.objects.update_or_create(
            mobile=mobile,
            defaults={
                'code': code,
                'attempts': 0,
                'expires_at': expires_at,
                'verified_at': None,
                'send_count': send_count,
                'send_window_started': send_window_started,
                'last_sent_at': now,
            },
        )

        from apps.users.services.otp_delivery import OTPDeliveryError, send_otp_code

        result = {
            'mobile': mobile,
            'expires_in': self.expiry,
            'resend_cooldown': self.resend_cooldown,
            'is_existing_user': User.objects.filter(mobile=mobile).exists(),
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

        logger.info('OTP stored in DB for %s, expires %s', mobile, expires_at.isoformat())
        return result

    def resend_otp(self, mobile: str) -> dict:
        mobile = normalize_mobile(mobile)
        challenge = self._get_challenge(mobile)
        if not challenge or challenge.is_verified:
            raise OTPError(
                'درخواست یافت نشد. لطفاً مجدداً شماره موبایل را وارد کنید.',
                code='not_found',
            )
        return self.send_otp(mobile)

    def verify_otp(self, mobile: str, code: str) -> dict:
        mobile = normalize_mobile(mobile)
        challenge = self._get_challenge(mobile)
        if not challenge:
            logger.warning('OTP verify failed: no challenge for %s', mobile)
            raise OTPError(
                'کد تأیید منقضی شده است. لطفاً مجدداً درخواست دهید.',
                code='expired',
            )

        if challenge.is_expired:
            challenge.delete()
            logger.warning('OTP verify failed: expired for %s', mobile)
            raise OTPError(
                'کد تأیید منقضی شده است. لطفاً مجدداً درخواست دهید.',
                code='expired',
            )

        challenge.attempts += 1

        if challenge.attempts > self.max_attempts:
            challenge.delete()
            raise OTPError(
                'تعداد تلاش‌های ناموفق بیش از حد مجاز است.',
                code='max_attempts',
            )

        if self._normalize_code(challenge.code) != self._normalize_code(code):
            challenge.save(update_fields=['attempts', 'updated_at'])
            raise OTPError('کد تأیید نادرست است.', code='invalid_code')

        user = User.objects.filter(mobile=mobile).first()
        if user:
            if not user.is_active:
                raise OTPError('حساب کاربری غیرفعال است.', code='inactive_user')
            challenge.delete()
            return {'action': 'login', 'user': user}

        challenge.verified_at = timezone.now()
        challenge.code = ''
        challenge.save(update_fields=['verified_at', 'code', 'updated_at'])
        return {'action': 'register', 'mobile': mobile}

    def _registration_deadline(self, challenge: OTPChallenge):
        return challenge.verified_at + timezone.timedelta(seconds=self.REGISTRATION_TTL)

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

        challenge = self._get_challenge(mobile)
        if not challenge or not challenge.is_verified or not challenge.verified_at:
            raise OTPError(
                'ابتدا کد تأیید را وارد کنید یا مجدداً درخواست دهید.',
                code='not_verified',
            )

        if timezone.now() >= self._registration_deadline(challenge):
            challenge.delete()
            raise OTPError(
                'مهلت تکمیل ثبت‌نام تمام شده است. لطفاً دوباره کد تأیید بگیرید.',
                code='registration_expired',
            )

        if User.objects.filter(mobile=mobile).exists():
            challenge.delete()
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
        challenge.delete()
        return user
