from django.db import migrations, models
from django.utils.text import slugify


DEFAULT_ASSOCIATIONS = [
    {
        'title': 'انجمن رباتیک',
        'description': 'طراحی، ساخت و برنامه‌نویسی ربات‌های آموزشی',
        'order': 1,
    },
    {
        'title': 'انجمن برنامه‌نویسی',
        'description': 'یادگیری زبان‌های برنامه‌نویسی و پروژه‌های نرم‌افزاری',
        'order': 2,
    },
    {
        'title': 'انجمن نجوم',
        'description': 'آشنایی با نجوم، رصد و پژوهش‌های نجومی',
        'order': 3,
    },
    {
        'title': 'انجمن زیست‌شناسی',
        'description': 'فعالیت‌های علمی و پژوهشی در حوزه علوم زیستی',
        'order': 4,
    },
]

DEFAULT_FESTIVALS = [
    {'title': 'ادبیات', 'slug': 'literature', 'order': 1},
    {'title': 'زیست فناوری', 'slug': 'biotech', 'order': 2},
    {'title': 'سلول‌های بنیادی', 'slug': 'stem-cells', 'order': 3},
    {'title': 'کد نویسی', 'slug': 'coding', 'order': 4},
    {'title': 'نجوم', 'slug': 'astronomy', 'order': 5},
    {'title': 'گیاهان دارویی', 'slug': 'medicinal-plants', 'order': 6},
    {'title': 'نانو', 'slug': 'nano', 'order': 7},
    {'title': 'آزمایشگاه', 'slug': 'laboratory', 'order': 8},
    {'title': 'حمل و نقل', 'slug': 'transport', 'order': 9},
]


def _assoc_content(title):
    return (
        f'انجمن {title} با هدف تقویت مهارت\u200cهای علمی و پژوهشی دانش\u200cآموزان '
        f'فعالیت می\u200cکند. برنامه\u200cها، کارگاه\u200cها و رویدادهای این انجمن از طریق '
        f'پنل مدیریت قابل به\u200cروزرسانی است.'
    )


def _festival_content(title):
    return (
        f'جشنواره {title} یکی از رویدادهای علمی پژوهش\u200cسرا است. '
        f'اطلاعات ثبت\u200cنام، زمان\u200cبندی و جزئیات از طریق این صفحه اطلاع\u200cرسانی می\u200cشود.'
    )


def seed_data(apps, schema_editor):
    Association = apps.get_model('content', 'Association')
    Festival = apps.get_model('content', 'Festival')

    for assoc in Association.objects.all():
        if not assoc.slug:
            base = slugify(assoc.title, allow_unicode=True) or f'association-{assoc.pk}'
            slug = base
            n = 1
            while Association.objects.filter(slug=slug).exclude(pk=assoc.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            assoc.slug = slug
        if not assoc.content:
            assoc.content = _assoc_content(assoc.title)
        assoc.save()

    if not Association.objects.exists():
        for item in DEFAULT_ASSOCIATIONS:
            slug = slugify(item['title'], allow_unicode=True)
            Association.objects.create(
                title=item['title'],
                slug=slug,
                description=item['description'],
                content=_assoc_content(item['title']),
                order=item['order'],
                is_active=True,
            )

    for fest in DEFAULT_FESTIVALS:
        Festival.objects.update_or_create(
            slug=fest['slug'],
            defaults={
                'title': fest['title'],
                'description': f'جشنواره تخصصی {fest["title"]} پژوهش\u200cسرا',
                'content': _festival_content(fest['title']),
                'order': fest['order'],
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='association',
            name='content',
            field=models.TextField(blank=True, help_text='متن کامل صفحه جزئیات', verbose_name='محتوای صفحه'),
        ),
        migrations.AddField(
            model_name='association',
            name='slug',
            field=models.SlugField(allow_unicode=True, max_length=255, null=True, unique=True, verbose_name='اسلاگ'),
        ),
        migrations.AlterField(
            model_name='association',
            name='description',
            field=models.TextField(help_text='متن کوتاه برای کارت انجمن', verbose_name='خلاصه'),
        ),
        migrations.CreateModel(
            name='Festival',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='عنوان')),
                ('slug', models.SlugField(allow_unicode=True, max_length=255, unique=True, verbose_name='اسلاگ')),
                ('description', models.TextField(help_text='متن کوتاه برای کارت جشنواره', verbose_name='خلاصه')),
                ('content', models.TextField(blank=True, help_text='متن کامل صفحه جزئیات', verbose_name='محتوای صفحه')),
                ('image', models.ImageField(blank=True, null=True, upload_to='festivals/', verbose_name='تصویر')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ترتیب')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
            ],
            options={
                'verbose_name': 'جشنواره',
                'verbose_name_plural': 'جشنواره\u200cها',
                'ordering': ['order', 'title'],
            },
        ),
        migrations.RunPython(seed_data, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='association',
            name='slug',
            field=models.SlugField(allow_unicode=True, max_length=255, unique=True, verbose_name='اسلاگ'),
        ),
    ]
