from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_add_gifted_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='schedule',
            field=models.TextField(
                blank=True,
                help_text='مثال: شنبه و دوشنبه · ۱۶:۰۰ تا ۱۸:۰۰',
                verbose_name='روزها و ساعت برگزاری',
            ),
        ),
    ]
