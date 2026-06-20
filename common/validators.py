import csv
import re

from django.core.exceptions import ValidationError

_PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
_ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'


def normalize_digits(value: str) -> str:
    """Convert Persian, Arabic, and fullwidth digits to ASCII 0-9."""
    if value is None:
        return ''
    result = []
    for char in str(value):
        if char in _PERSIAN_DIGITS:
            result.append(str(_PERSIAN_DIGITS.index(char)))
        elif char in _ARABIC_DIGITS:
            result.append(str(_ARABIC_DIGITS.index(char)))
        elif '0' <= char <= '9':
            result.append(char)
        elif '\uff10' <= char <= '\uff19':
            result.append(chr(ord(char) - 0xFEE0))
    return ''.join(result)


def validate_iranian_national_code(value: str) -> None:
    """Validate Iranian national code (کد ملی) using check digit algorithm."""
    value = normalize_digits(value)
    if not re.match(r'^\d{10}$', value):
        raise ValidationError('کد ملی باید ۱۰ رقم باشد.')

    if len(set(value)) == 1:
        raise ValidationError('کد ملی نامعتبر است.')

    check_digit = int(value[9])
    total = sum(int(value[i]) * (10 - i) for i in range(9))
    remainder = total % 11

    if remainder < 2:
        if check_digit != remainder:
            raise ValidationError('کد ملی نامعتبر است.')
    elif check_digit != 11 - remainder:
        raise ValidationError('کد ملی نامعتبر است.')


def validate_iranian_mobile(value: str) -> None:
    """Validate Iranian mobile number format (09xxxxxxxxx)."""
    if not re.match(r'^09\d{9}$', value):
        raise ValidationError('شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد.')


def normalize_mobile(value: str) -> str:
    """Normalize mobile number to 09xxxxxxxxx format."""
    digits = re.sub(r'\D', '', value)
    if digits.startswith('98') and len(digits) == 12:
        digits = '0' + digits[2:]
    elif digits.startswith('9') and len(digits) == 10:
        digits = '0' + digits
    return digits
