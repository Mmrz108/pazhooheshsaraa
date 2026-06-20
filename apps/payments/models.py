from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'در انتظار'
    SUCCESSFUL = 'successful', 'موفق'
    FAILED = 'failed', 'ناموفق'


class PaymentGateway(models.TextChoices):
    ZARINPAL = 'zarinpal', 'زرین‌پال'


class Payment(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='کاربر',
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='دوره',
    )
    amount = models.PositiveIntegerField('مبلغ (تومان)')
    authority = models.CharField('Authority', max_length=64, blank=True, db_index=True)
    ref_id = models.CharField('Ref ID', max_length=64, blank=True)
    gateway = models.CharField(
        'درگاه',
        max_length=20,
        choices=PaymentGateway.choices,
        default=PaymentGateway.ZARINPAL,
    )
    status = models.CharField(
        'وضعیت',
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.course} - {self.amount}'
