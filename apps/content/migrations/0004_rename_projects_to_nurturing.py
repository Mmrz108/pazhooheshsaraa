from django.db import migrations


def rename_projects_to_nurturing(apps, schema_editor):
    Academy = apps.get_model('content', 'Academy')
    Academy.objects.filter(slug='projects').update(
        title='پرورشی',
        slug='nurturing',
        description='برنامه‌های پرورشی و رشد فردی دانش‌آموزان',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_academy_pages'),
    ]

    operations = [
        migrations.RunPython(rename_projects_to_nurturing, migrations.RunPython.noop),
    ]
