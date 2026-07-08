from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_course_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='registration_deadline',
            field=models.DateField(
                blank=True,
                help_text='پس از این تاریخ دوره در سایت نمایش داده نمی‌شود.',
                null=True,
                verbose_name='فرصت ثبت\u200cنام تا',
            ),
        ),
    ]
