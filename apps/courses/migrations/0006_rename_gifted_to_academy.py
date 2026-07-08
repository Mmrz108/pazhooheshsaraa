from django.db import migrations


def rename_gifted_to_academy(apps, schema_editor):
    CourseCategory = apps.get_model('courses', 'CourseCategory')
    gifted = CourseCategory.objects.filter(slug='gifted').first()
    if not gifted:
        CourseCategory.objects.update_or_create(
            slug='academy',
            defaults={
                'title': 'آکادمی',
                'description': 'دوره‌های آکادمی و آمادگی تخصصی دانش‌آموزان',
                'meta_title': 'دوره‌های آکادمی | پژوهش‌سرا',
                'meta_description': 'دوره‌های آکادمی پژوهش‌سرا برای تقویت مهارت‌ها و آمادگی علمی.',
                'order': 2,
                'is_active': True,
            },
        )
        return
    if CourseCategory.objects.filter(slug='academy').exclude(pk=gifted.pk).exists():
        gifted.delete()
        return
    gifted.slug = 'academy'
    gifted.title = 'آکادمی'
    gifted.description = 'دوره‌های آکادمی و آمادگی تخصصی دانش‌آموزان'
    gifted.meta_title = 'دوره‌های آکادمی | پژوهش‌سرا'
    gifted.meta_description = 'دوره‌های آکادمی پژوهش‌سرا برای تقویت مهارت‌ها و آمادگی علمی.'
    gifted.order = 2
    gifted.save()


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_seed_course_categories'),
    ]

    operations = [
        migrations.RunPython(rename_gifted_to_academy, migrations.RunPython.noop),
    ]
