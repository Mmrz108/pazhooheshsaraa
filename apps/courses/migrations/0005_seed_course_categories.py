from django.db import migrations


DEFAULT_CATEGORIES = [
    {
        'slug': 'extracurricular',
        'title': 'فوق برنامه',
        'description': 'دوره‌های فوق برنامه علمی، فناوری و مهارتی پژوهش‌سرا',
        'meta_title': 'دوره‌های فوق برنامه | پژوهش‌سرا',
        'meta_description': 'ثبت‌نام در دوره‌های فوق برنامه برنامه‌نویسی، رباتیک، هوش مصنوعی و مهارت‌های فناورانه در پژوهش‌سرا.',
        'order': 1,
    },
    {
        'slug': 'gifted',
        'title': 'تیزهوشان',
        'description': 'دوره‌های آمادگی و تقویت برای آزمون‌های تیزهوشان',
        'meta_title': 'دوره‌های تیزهوشان | پژوهش‌سرا',
        'meta_description': 'بهترین دوره‌های آمادگی تیزهوشان با اساتید مجرب در پژوهش‌سرا. ثبت‌نام آنلاین.',
        'order': 2,
    },
    {
        'slug': 'olympiad',
        'title': 'المپیاد',
        'description': 'دوره‌های تخصصی آمادگی المپیادهای علمی کشور',
        'meta_title': 'دوره‌های المپیاد | پژوهش‌سرا',
        'meta_description': 'آمادگی کامل برای المپیاد ریاضی، کامپیوتر، فیزیک و سایر رشته‌ها در پژوهش‌سرا.',
        'order': 3,
    },
    {
        'slug': 'support',
        'title': 'تقویتی',
        'description': 'دوره‌های تقویتی درسی برای تقویت پایه علمی دانش‌آموزان',
        'meta_title': 'دوره‌های تقویتی | پژوهش‌سرا',
        'meta_description': 'کلاس‌های تقویتی دروس پایه و تخصصی برای ارتقای عملکرد تحصیلی در پژوهش‌سرا.',
        'order': 4,
    },
]

SLUG_RENAMES = {
    'فوق-برنامه': 'extracurricular',
    'فوق برنامه': 'extracurricular',
    'تیزهوشان': 'gifted',
    'المپیاد': 'olympiad',
    'تقویتی': 'support',
}


def seed_categories(apps, schema_editor):
    CourseCategory = apps.get_model('courses', 'CourseCategory')

    for old_slug, new_slug in SLUG_RENAMES.items():
        old_cat = CourseCategory.objects.filter(slug=old_slug).first()
        if not old_cat:
            continue
        if CourseCategory.objects.filter(slug=new_slug).exclude(pk=old_cat.pk).exists():
            old_cat.delete()
        else:
            old_cat.slug = new_slug
            old_cat.save(update_fields=['slug'])

    for cat in DEFAULT_CATEGORIES:
        CourseCategory.objects.update_or_create(
            slug=cat['slug'],
            defaults={**cat, 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_coursecategory_course_category'),
    ]

    operations = [
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
