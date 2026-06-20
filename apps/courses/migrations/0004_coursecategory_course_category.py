import django.db.models.deletion
from django.db import migrations, models


def create_categories(apps, schema_editor):
    CourseCategory = apps.get_model('courses', 'CourseCategory')
    categories = [
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
    for cat in categories:
        CourseCategory.objects.get_or_create(slug=cat['slug'], defaults=cat)


def assign_default_category(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    CourseCategory = apps.get_model('courses', 'CourseCategory')
    default = CourseCategory.objects.filter(slug='extracurricular').first()
    if default:
        Course.objects.filter(category__isnull=True).update(category=default)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='عنوان')),
                ('slug', models.SlugField(allow_unicode=True, max_length=100, unique=True, verbose_name='اسلاگ')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('meta_title', models.CharField(blank=True, max_length=255, verbose_name='عنوان SEO')),
                ('meta_description', models.TextField(blank=True, verbose_name='توضیحات SEO')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ترتیب')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
            ],
            options={
                'verbose_name': 'دسته\u200cبندی دوره',
                'verbose_name_plural': 'دسته\u200cبندی دوره\u200cها',
                'ordering': ['order', 'title'],
            },
        ),
        migrations.RunPython(create_categories, migrations.RunPython.noop),
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='courses',
                to='courses.coursecategory',
                verbose_name='دسته\u200cبندی',
            ),
        ),
        migrations.RunPython(assign_default_category, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='course',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='courses',
                to='courses.coursecategory',
                verbose_name='دسته\u200cبندی',
            ),
        ),
    ]
