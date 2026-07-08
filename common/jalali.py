from datetime import date, datetime

import jdatetime

_DIGIT_MAP = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')


def to_jalali_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        value = value.date()
    return jdatetime.date.fromgregorian(date=value)


def format_jalali_date(value, fmt='%Y/%m/%d'):
    jalali = to_jalali_date(value)
    return jalali.strftime(fmt) if jalali else '-'


def format_jalali_datetime(value, fmt='%Y/%m/%d %H:%M'):
    if not value:
        return '-'
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    jalali = jdatetime.datetime.fromgregorian(datetime=value)
    return jalali.strftime(fmt)


def parse_jalali_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value

    text = str(value).strip().translate(_DIGIT_MAP)
    for sep in ('/', '-'):
        parts = text.split(sep)
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            year, month, day = (int(part) for part in parts)
            return jdatetime.date(year, month, day).togregorian()
    raise ValueError('فرمت تاریخ شمسی نامعتبر است. مثال: 1385/03/15')
