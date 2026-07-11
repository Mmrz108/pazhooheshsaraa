"""Parse psdnj.ir course export for database seeding."""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COURSES_JSON = PROJECT_ROOT / 'psdnj_courses.json'

EXTRACURRICULAR_KEYWORDS = (
    'ربات', 'برنامه نویسی', 'برنامه‌نویسی', 'کدنویسی', 'اسکرچ', 'پایتون',
    'python', 'html', 'css', 'هوش مصنوعی', 'icdl', 'گیم', 'طراحی بازی',
    'آزمایشگر', 'نجوم', 'نانو', 'کامپیوتر', 'arduino', 'آردوینو',
)
GIFTED_KEYWORDS = ('تیزهوش', 'سمپاد', 'استعدادهای درخشان')
OLYMPIAD_KEYWORDS = ('المپیاد', 'olympiad')
ACADEMY_KEYWORDS = ('آکادمی', 'مشاوره تحصیلی', 'کارآفرینی', 'روانشناسی')

SCHEDULE_PATTERNS = (
    re.compile(r'(?:📅\s*)?روز و ساعت[:\s]*([^\n]+)', re.I),
    re.compile(r'(?:📅\s*)?روزهای برگزاری[:\s]*([^\n]+)', re.I),
    re.compile(r'(?:📅\s*)?روز برگزاری[:\s]*([^\n]+)', re.I),
    re.compile(r'روز و ساعت[:\s]*([^\n]+)', re.I),
)

PRICE_PATTERNS = (
    re.compile(r'(?:💰\s*)?(?:شهریه|هزینه)(?:\s+ثبت‌نام|\s+دوره)?[:\s]*([۰-۹\d,\.]+)\s*(?:هزار\s*)?تومان', re.I),
    re.compile(r'قیمت[:\s]*([۰-۹\d,\.]+)\s*تومان', re.I),
)

PERSIAN_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')


def clean_description(raw: str) -> str:
    text = (raw or '').replace('\\r\\n', '\n').replace('\\n', '\n').replace('\\r', '\n')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'(?<=[!.:؟!])\s*rn(?=\S)', '\n', text)
    text = re.sub(r'\s*rn\s*', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_schedule(description: str) -> str:
    for pattern in SCHEDULE_PATTERNS:
        match = pattern.search(description)
        if match:
            return match.group(1).strip().rstrip('rn').strip()
    return ''


def extract_price(description: str) -> int:
    for pattern in PRICE_PATTERNS:
        match = pattern.search(description)
        if not match:
            continue
        raw = match.group(1).translate(PERSIAN_DIGITS).replace(',', '').replace('.', '')
        if 'هزار' in match.group(0):
            try:
                return int(raw) * 1000
            except ValueError:
                continue
        try:
            return int(raw)
        except ValueError:
            continue
    return 0


def extract_capacity(description: str) -> int | None:
    match = re.search(
        r'ظرفیت(?:\s+کلاس)?[:\s]*([۰-۹\d]+)\s*(?:تا\s*([۰-۹\d]+)\s*)?نفر',
        description,
    )
    if not match:
        return None
    hi = match.group(2) or match.group(1)
    try:
        return int(hi.translate(PERSIAN_DIGITS))
    except ValueError:
        return None


def extract_course_code(title: str) -> str:
    match = re.match(r'^([A-Za-z0-9]+)\s*-\s*', title.strip())
    return match.group(1).lower() if match else ''


def infer_category_slug(title: str, description: str) -> str:
    haystack = f'{title} {description[:400]}'.lower()
    if any(k in haystack for k in OLYMPIAD_KEYWORDS):
        return 'olympiad'
    if any(k in haystack for k in GIFTED_KEYWORDS):
        return 'gifted'
    if title.strip().lower().startswith(('a',)) and re.match(r'^a\d+', title.strip(), re.I):
        return 'extracurricular'
    if any(k in haystack for k in EXTRACURRICULAR_KEYWORDS):
        return 'extracurricular'
    if any(k in haystack for k in ACADEMY_KEYWORDS):
        return 'academy'
    return 'support'


def infer_age_group(title: str, description: str) -> str:
    haystack = f'{title} {description[:500]}'
    if any(k in haystack for k in ('والدین', 'همکاران', 'بزرگسال')):
        return 'adults'
    if any(k in haystack for k in ('پنجم', 'ششم', 'هفتم', 'هشتم', 'کودک', '۶ تا', '۷ تا', '۸ تا', '۹ تا', '۱۰ تا')):
        if any(k in haystack for k in ('دوازدهم', 'یازدهم', 'دهم', 'نهم', 'متوسطه', '۱۷ سال', '۱۸ سال', '۲۰ سال')):
            return 'teens'
        return 'children'
    if any(k in haystack for k in ('دهم', 'یازدهم', 'دوازدهم', 'نهم', 'نوجوان', 'متوسطه')):
        return 'teens'
    return 'all'


def infer_level(title: str, description: str) -> str:
    haystack = f'{title} {description[:300]}'
    if any(k in haystack for k in ('پیشرفته', 'advanced')):
        return 'advanced'
    if any(k in haystack for k in ('متوسط', 'intermediate')):
        return 'intermediate'
    return 'beginner'


def make_slug(course_id: int, title: str) -> str:
    code = extract_course_code(title)
    if code:
        return f'psdnj-{code}'
    return f'psdnj-{course_id}'


def load_courses_data(json_path: Path | None = None) -> list[dict]:
    path = json_path or COURSES_JSON
    with path.open(encoding='utf-8') as fh:
        return json.load(fh)


def build_course_defaults(
    item: dict,
    category_id: int,
    *,
    start: date | None = None,
    priority: int = 100,
) -> dict:
    title = (item.get('title') or '').strip()
    description = clean_description(item.get('description', ''))
    schedule = extract_schedule(description)
    today = start or date.today()

    return {
        'title': title,
        'description': description,
        'category_id': category_id,
        'price': extract_price(description),
        'capacity': extract_capacity(description) or 20,
        'schedule': schedule,
        'age_group': infer_age_group(title, description),
        'level': infer_level(title, description),
        'start_date': today,
        'end_date': today + timedelta(days=120),
        'registration_deadline': today + timedelta(days=45),
        'priority': priority,
        'is_active': True,
    }
