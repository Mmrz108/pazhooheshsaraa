from django.db import models
from django.utils.text import slugify


class CourseCategory(models.Model):
    title = models.CharField('عنوان', max_length=100)
    slug = models.SlugField('اسلاگ', max_length=100, unique=True, allow_unicode=True)
    description = models.TextField('توضیحات', blank=True)
    meta_title = models.CharField('عنوان SEO', max_length=255, blank=True)
    meta_description = models.TextField('توضیحات SEO', blank=True)
    order = models.PositiveIntegerField('ترتیب', default=0)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'دسته‌بندی دوره'
        verbose_name_plural = 'دسته‌بندی دوره‌ها'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        if not self.meta_title:
            self.meta_title = f'دوره‌های {self.title} | پژوهش‌سرا'
        super().save(*args, **kwargs)


class AgeGroup(models.TextChoices):
    CHILDREN = 'children', 'کودکان'
    TEENS = 'teens', 'نوجوانان'
    ADULTS = 'adults', 'بزرگسالان'
    ALL = 'all', 'همه سنین'


class CourseLevel(models.TextChoices):
    BEGINNER = 'beginner', 'مقدماتی'
    INTERMEDIATE = 'intermediate', 'متوسط'
    ADVANCED = 'advanced', 'پیشرفته'


class Course(models.Model):
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='دسته‌بندی',
    )
    title = models.CharField('عنوان', max_length=255)
    slug = models.SlugField('اسلاگ', max_length=255, unique=True, allow_unicode=True)
    description = models.TextField('توضیحات')
    image = models.ImageField('تصویر', upload_to='courses/', blank=True, null=True)
    price = models.PositiveIntegerField('قیمت (تومان)')
    age_group = models.CharField(
        'گروه سنی',
        max_length=20,
        choices=AgeGroup.choices,
        default=AgeGroup.ALL,
    )
    level = models.CharField(
        'سطح',
        max_length=20,
        choices=CourseLevel.choices,
        default=CourseLevel.BEGINNER,
    )
    capacity = models.PositiveIntegerField('ظرفیت')
    start_date = models.DateField('تاریخ شروع')
    end_date = models.DateField('تاریخ پایان')
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'دوره'
        verbose_name_plural = 'دوره‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status=EnrollmentStatus.PAID).count()

    @property
    def remaining_capacity(self):
        return max(0, self.capacity - self.enrolled_count)

    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity


class EnrollmentStatus(models.TextChoices):
    PENDING = 'pending', 'در انتظار'
    PAID = 'paid', 'پرداخت شده'
    CANCELLED = 'cancelled', 'لغو شده'


class Enrollment(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='کاربر',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='دوره',
    )
    payment = models.OneToOneField(
        'payments.Payment',
        on_delete=models.PROTECT,
        related_name='enrollment',
        verbose_name='پرداخت',
        null=True,
        blank=True,
    )
    enrollment_date = models.DateTimeField('تاریخ ثبت‌نام', auto_now_add=True)
    status = models.CharField(
        'وضعیت',
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.PENDING,
    )

    class Meta:
        verbose_name = 'ثبت‌نام'
        verbose_name_plural = 'ثبت‌نام‌ها'
        ordering = ['-enrollment_date']
        unique_together = [('user', 'course')]

    def __str__(self):
        return f'{self.user} - {self.course}'
