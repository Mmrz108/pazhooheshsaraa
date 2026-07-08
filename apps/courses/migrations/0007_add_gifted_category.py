from django.db import migrations


def add_gifted_category(apps, schema_editor):
    CourseCategory = apps.get_model('courses', 'CourseCategory')

    CourseCategory.objects.filter(slug='academy').update(order=3)
    CourseCategory.objects.filter(slug='olympiad').update(order=4)
    CourseCategory.objects.filter(slug='support').update(order=5)

    CourseCategory.objects.update_or_create(
        slug='gifted',
        defaults={
            'title': 'تیزهوشان',
            'description': 'دوره‌های آمادگی و تقویت برای آزمون‌های تیزهوشان',
            'meta_title': 'دوره‌های تیزهوشان | پژوهش\u200cسرا',
            'meta_description': 'بهترین دوره‌های آمادگی تیزهوشان با اساتید مجرب در پژوهش\u200cسرا. ثبت\u200cنام آنلاین.',
            'order': 2,
            'is_active': True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_rename_gifted_to_academy'),
    ]

    operations = [
        migrations.RunPython(add_gifted_category, migrations.RunPython.noop),
    ]
