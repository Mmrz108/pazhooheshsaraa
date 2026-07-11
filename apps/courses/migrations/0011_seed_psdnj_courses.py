import json
from datetime import date
from pathlib import Path

from django.db import migrations

from apps.courses.psdnj_import import (
    build_course_defaults,
    infer_category_slug,
    make_slug,
)


def _load_json():
    path = Path(__file__).resolve().parents[3] / 'psdnj_courses.json'
    with path.open(encoding='utf-8') as fh:
        return json.load(fh)


def seed_psdnj_courses(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    CourseCategory = apps.get_model('courses', 'CourseCategory')
    Enrollment = apps.get_model('courses', 'Enrollment')
    Payment = apps.get_model('payments', 'Payment')

    Enrollment.objects.all().delete()
    Payment.objects.all().delete()
    Course.objects.all().delete()

    categories = {
        cat.slug: cat
        for cat in CourseCategory.objects.filter(is_active=True)
    }
    default_category = categories.get('support') or CourseCategory.objects.first()
    if not default_category:
        raise RuntimeError('No course categories found; run category seed migrations first.')

    items = sorted(_load_json(), key=lambda x: (x.get('title') or ''))
    today = date.today()
    used_slugs: set[str] = set()

    for index, item in enumerate(items, start=1):
        title = (item.get('title') or '').strip()
        if not title:
            continue

        category_slug = infer_category_slug(title, item.get('description', ''))
        category = categories.get(category_slug, default_category)

        base_slug = make_slug(item['id'], title)
        slug = base_slug
        suffix = 2
        while slug in used_slugs or Course.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{suffix}'
            suffix += 1
        used_slugs.add(slug)

        defaults = build_course_defaults(
            item,
            category.pk,
            start=today,
            priority=index,
        )
        Course.objects.create(slug=slug, **defaults)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_course_priority'),
        ('payments', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(seed_psdnj_courses, migrations.RunPython.noop),
    ]
