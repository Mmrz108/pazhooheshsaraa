from django.db import models
from django.utils.text import slugify


class ArticleCategory(models.Model):
    title = models.CharField('عنوان', max_length=255)
    slug = models.SlugField('اسلاگ', max_length=255, unique=True, allow_unicode=True)

    class Meta:
        verbose_name = 'دسته‌بندی مقاله'
        verbose_name_plural = 'دسته‌بندی مقالات'
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class Article(models.Model):
    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='دسته‌بندی',
    )
    title = models.CharField('عنوان', max_length=255)
    slug = models.SlugField('اسلاگ', max_length=255, unique=True, allow_unicode=True)
    excerpt = models.TextField('خلاصه', blank=True)
    content = models.TextField('محتوا')
    image = models.ImageField('تصویر', upload_to='articles/', blank=True, null=True)
    publish_date = models.DateTimeField('تاریخ انتشار')
    is_published = models.BooleanField('منتشر شده', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'
        ordering = ['-publish_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class Association(models.Model):
    title = models.CharField('عنوان', max_length=255)
    slug = models.SlugField('اسلاگ', max_length=255, unique=True, allow_unicode=True)
    description = models.TextField('خلاصه', help_text='متن کوتاه برای کارت انجمن')
    content = models.TextField('محتوای صفحه', blank=True, help_text='متن کامل صفحه جزئیات')
    image = models.ImageField('تصویر', upload_to='associations/', blank=True, null=True)
    order = models.PositiveIntegerField('ترتیب', default=0)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'انجمن'
        verbose_name_plural = 'انجمن‌ها'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        if not self.content:
            self.content = (
                f'انجمن {self.title} با هدف تقویت مهارت\u200cهای علمی و پژوهشی دانش\u200cآموزان '
                f'فعالیت می\u200cکند. برنامه\u200cها، کارگاه\u200cها و رویدادهای این انجمن از طریق '
                f'پنل مدیریت قابل به\u200cروزرسانی است.'
            )
        super().save(*args, **kwargs)


class Festival(models.Model):
    title = models.CharField('عنوان', max_length=255)
    slug = models.SlugField('اسلاگ', max_length=255, unique=True, allow_unicode=True)
    description = models.TextField('خلاصه', help_text='متن کوتاه برای کارت جشنواره')
    content = models.TextField('محتوای صفحه', blank=True, help_text='متن کامل صفحه جزئیات')
    image = models.ImageField('تصویر', upload_to='festivals/', blank=True, null=True)
    order = models.PositiveIntegerField('ترتیب', default=0)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'جشنواره'
        verbose_name_plural = 'جشنواره‌ها'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        if not self.content:
            self.content = (
                f'جشنواره {self.title} یکی از رویدادهای علمی پژوهش\u200cسرا است. '
                f'اطلاعات ثبت\u200cنام، زمان\u200cبندی و جزئیات از طریق این صفحه اطلاع\u200cرسانی می\u200cشود.'
            )
        super().save(*args, **kwargs)


class GalleryCategory(models.Model):
    title = models.CharField('عنوان', max_length=255)
    slug = models.SlugField('اسلاگ', max_length=255, unique=True, allow_unicode=True)
    order = models.PositiveIntegerField('ترتیب', default=0)

    class Meta:
        verbose_name = 'دسته‌بندی گالری'
        verbose_name_plural = 'دسته‌بندی‌های گالری'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class GalleryImage(models.Model):
    category = models.ForeignKey(
        GalleryCategory,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='دسته‌بندی',
    )
    title = models.CharField('عنوان', max_length=255, blank=True)
    image = models.ImageField('تصویر', upload_to='gallery/')
    order = models.PositiveIntegerField('ترتیب', default=0)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'تصویر گالری'
        verbose_name_plural = 'تصاویر گالری'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f'Image #{self.pk}'


class SiteSettings(models.Model):
    logo = models.ImageField('لوگو', upload_to='site/', blank=True, null=True)
    hero_image = models.ImageField('تصویر هیرو', upload_to='site/', blank=True, null=True)
    about_text = models.TextField('درباره ما', blank=True)
    phone = models.CharField('تلفن', max_length=20, blank=True)
    email = models.EmailField('ایمیل', blank=True)
    address = models.TextField('آدرس', blank=True)
    eitaa_link = models.URLField('لینک ایتا', blank=True)

    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def __str__(self):
        return 'تنظیمات سایت'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def delete(self, *args, **kwargs):
        pass
