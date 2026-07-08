from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_PATH = Path(settings.BASE_DIR) / 'static' / 'fonts' / 'Vazirmatn-Regular.ttf'
_FONT_REGISTERED = False


def _register_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return 'Vazirmatn' if FONT_PATH.exists() else 'Helvetica'
    if FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont('Vazirmatn', str(FONT_PATH)))
        _FONT_REGISTERED = True
        return 'Vazirmatn'
    _FONT_REGISTERED = True
    return 'Helvetica'


def _fa(text):
    if text is None:
        return ''
    text = str(text)
    if not text:
        return ''
    return get_display(arabic_reshaper.reshape(text))


def _format_date(dt):
    if not dt:
        return '-'
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime('%Y/%m/%d %H:%M')


def build_course_enrollments_pdf(course, enrollments):
    font_name = _register_font()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=_fa(f'ثبت\u200cنام {course.title}'),
    )

    title_style = ParagraphStyle(
        'Title',
        fontName=font_name,
        fontSize=14,
        leading=20,
        alignment=2,
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        'Meta',
        fontName=font_name,
        fontSize=10,
        leading=14,
        alignment=2,
        textColor=colors.HexColor('#475569'),
        spaceAfter=14,
    )
    cell_style = ParagraphStyle(
        'Cell',
        fontName=font_name,
        fontSize=9,
        leading=13,
        alignment=2,
    )

    story = [
        Paragraph(_fa(f'لیست ثبت\u200cنام دوره: {course.title}'), title_style),
        Paragraph(
            _fa(
                f'دسته: {course.category.title if course.category_id else "-"} · '
                f'تعداد: {len(enrollments)} · '
                f'تاریخ گزارش: {_format_date(timezone.now())}'
            ),
            meta_style,
        ),
    ]

    headers = [
        Paragraph(_fa('ردیف'), cell_style),
        Paragraph(_fa('نام و نام خانوادگی'), cell_style),
        Paragraph(_fa('موبایل'), cell_style),
        Paragraph(_fa('کد ملی'), cell_style),
        Paragraph(_fa('نام پدر'), cell_style),
        Paragraph(_fa('وضعیت'), cell_style),
        Paragraph(_fa('تاریخ ثبت\u200cنام'), cell_style),
    ]
    rows = [headers]

    for index, enrollment in enumerate(enrollments, start=1):
        user = enrollment.user
        rows.append([
            Paragraph(str(index), cell_style),
            Paragraph(_fa(user.full_name), cell_style),
            Paragraph(user.mobile, cell_style),
            Paragraph(user.national_code, cell_style),
            Paragraph(_fa(user.father_name or '-'), cell_style),
            Paragraph(_fa(enrollment.get_status_display()), cell_style),
            Paragraph(_format_date(enrollment.enrollment_date), cell_style),
        ])

    table = Table(rows, repeatRows=1, colWidths=[28, 95, 72, 72, 72, 58, 78])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2FF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 8 * mm))

    doc.build(story)
    buffer.seek(0)
    return buffer
