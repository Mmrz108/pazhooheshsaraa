from django.db import migrations, models


DEFAULT_ACADEMIES = [
    {
        'title': 'پروژه',
        'slug': 'projects',
        'description': 'اجرای پروژه‌های علمی و کاربردی با راهنمایی اساتید',
        'order': 1,
    },
    {
        'title': 'استعدادیابی',
        'slug': 'talent-discovery',
        'description': 'شناسایی و پرورش استعدادهای علمی و فناوری دانش‌آموزان',
        'order': 2,
    },
    {
        'title': 'روانشناسی',
        'slug': 'psychology',
        'description': 'مشاوره روانشناختی و تقویت سلامت ذهنی دانش‌آموزان',
        'order': 3,
    },
    {
        'title': 'کارآفرینی',
        'slug': 'entrepreneurship',
        'description': 'آموزش مهارت‌های کسب‌وکار و نوآوری برای نسل آینده',
        'order': 4,
    },
    {
        'title': 'مشاوره تحصیلی',
        'slug': 'academic-counseling',
        'description': 'راهنمایی انتخاب رشته، برنامه‌ریزی درسی و مسیر تحصیلی',
        'order': 5,
    },
    {
        'title': 'خلاقیت و نوآوری',
        'slug': 'creativity',
        'description': 'پرورش تفکر خلاق و حل مسئله در حوزه‌های علمی',
        'order': 6,
    },
    {
        'title': 'مهارت‌های اجتماعی',
        'slug': 'social-skills',
        'description': 'تقویت ارتباط مؤثر، کار گروهی و رهبری',
        'order': 7,
    },
]


def _academy_content(title):
    return (
        f'برنامه {title} بخشی از آکادمی پژوهش\u200cسرا است. '
        f'اطلاعات ثبت\u200cنام، زمان\u200cبندی و جزئیات از طریق این صفحه اطلاع\u200cرسانی می\u200cشود.'
    )


def seed_academies(apps, schema_editor):
    Academy = apps.get_model('content', 'Academy')
    for item in DEFAULT_ACADEMIES:
        Academy.objects.update_or_create(
            slug=item['slug'],
            defaults={
                'title': item['title'],
                'description': item['description'],
                'content': _academy_content(item['title']),
                'order': item['order'],
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_association_festival_pages'),
    ]

    operations = [
        migrations.CreateModel(
            name='Academy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='عنوان')),
                ('slug', models.SlugField(allow_unicode=True, max_length=255, unique=True, verbose_name='اسلاگ')),
                ('description', models.TextField(help_text='متن کوتاه برای کارت آکادمی', verbose_name='خلاصه')),
                ('content', models.TextField(blank=True, help_text='متن کامل صفحه جزئیات', verbose_name='محتوای صفحه')),
                ('image', models.ImageField(blank=True, null=True, upload_to='academies/', verbose_name='تصویر')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ترتیب')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
            ],
            options={
                'verbose_name': 'برنامه آکادمی',
                'verbose_name_plural': 'برنامه\u200cهای آکادمی',
                'ordering': ['order', 'title'],
            },
        ),
        migrations.RunPython(seed_academies, migrations.RunPython.noop),
    ]
