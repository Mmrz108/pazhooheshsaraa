from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_course_registration_deadline'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='priority',
            field=models.PositiveIntegerField(
                default=100,
                help_text='عدد کوچکتر = نمایش جلوتر در صفحه اصلی (۱ بالاترین اولویت).',
                verbose_name='اولویت',
            ),
        ),
        migrations.AlterModelOptions(
            name='course',
            options={
                'ordering': ['priority', '-created_at'],
                'verbose_name': 'دوره',
                'verbose_name_plural': 'دوره‌ها',
            },
        ),
    ]
