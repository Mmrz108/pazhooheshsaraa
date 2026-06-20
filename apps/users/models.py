from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.validators import validate_iranian_mobile, validate_iranian_national_code


class UserManager(BaseUserManager):
    def create_user(self, mobile, first_name, last_name, national_code, **extra_fields):
        if not mobile:
            raise ValueError('شماره موبایل الزامی است.')
        user = self.model(
            mobile=mobile,
            first_name=first_name,
            last_name=last_name,
            national_code=national_code,
            **extra_fields,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, first_name, last_name, national_code, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(mobile, first_name, last_name, national_code, **extra_fields)
        if password:
            user.set_password(password)
            user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField('نام', max_length=150)
    last_name = models.CharField('نام خانوادگی', max_length=150)
    national_code = models.CharField(
        'کد ملی',
        max_length=10,
        unique=True,
        validators=[validate_iranian_national_code],
    )
    mobile = models.CharField(
        'شماره موبایل',
        max_length=11,
        unique=True,
        validators=[validate_iranian_mobile],
    )
    father_name = models.CharField('نام پدر', max_length=150, blank=True, default='')
    birth_date = models.DateField('تاریخ تولد', null=True, blank=True)
    is_active = models.BooleanField('فعال', default=True)
    is_staff = models.BooleanField('کارمند', default=False)
    date_joined = models.DateTimeField('تاریخ عضویت', default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'national_code']

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.mobile})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class OTPChallenge(models.Model):
    mobile = models.CharField('شماره موبایل', max_length=11, unique=True, db_index=True)
    code = models.CharField('کد OTP', max_length=6)
    attempts = models.PositiveSmallIntegerField('تعداد تلاش', default=0)
    expires_at = models.DateTimeField('انقضای کد')
    verified_at = models.DateTimeField('زمان تأیید', null=True, blank=True)
    send_count = models.PositiveSmallIntegerField('تعداد ارسال', default=1)
    send_window_started = models.DateTimeField('شروع پنجره ارسال', default=timezone.now)
    last_sent_at = models.DateTimeField('آخرین ارسال', default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'چالش OTP'
        verbose_name_plural = 'چالش‌های OTP'

    def __str__(self):
        return self.mobile

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_verified(self):
        return self.verified_at is not None
