import csv

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.utils.html import format_html_join

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'mobile', 'full_name_display', 'national_code',
        'is_active', 'enrollment_count', 'total_payments_display',
        'date_joined',
    ]
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['mobile', 'first_name', 'last_name', 'national_code']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login', 'enrollment_list', 'payment_history']
    actions = ['export_users_csv']

    fieldsets = (
        (None, {'fields': ('mobile', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'national_code', 'father_name', 'birth_date')}),
        ('دوره‌ها و پرداخت‌ها', {'fields': ('enrollment_list', 'payment_history')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'mobile', 'first_name', 'last_name', 'national_code',
                'father_name', 'birth_date', 'password1', 'password2',
            ),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _enrollment_count=Count('enrollments', distinct=True),
            _total_payments=Sum('payments__amount', filter=Q(payments__status='successful')),
        )

    @admin.display(description='نام کامل')
    def full_name_display(self, obj):
        return obj.full_name

    @admin.display(description='تعداد دوره‌ها', ordering='_enrollment_count')
    def enrollment_count(self, obj):
        return obj._enrollment_count

    @admin.display(description='مجموع پرداخت‌ها')
    def total_payments_display(self, obj):
        total = obj._total_payments or 0
        return f'{total:,} تومان'

    @admin.display(description='دوره‌های ثبت‌نام‌شده')
    def enrollment_list(self, obj):
        enrollments = obj.enrollments.select_related('course').all()
        if not enrollments:
            return '-'
        return format_html_join(
            '', '<li>{} ({})</li>',
            ((e.course.title, e.get_status_display()) for e in enrollments),
        )

    @admin.display(description='تاریخچه پرداخت')
    def payment_history(self, obj):
        payments = obj.payments.select_related('course').order_by('-created_at')[:20]
        if not payments:
            return '-'
        rows = format_html_join(
            '', '<tr><td>{}</td><td>{:,}</td><td>{}</td><td>{}</td></tr>',
            (
                (p.course.title, p.amount, p.get_status_display(), p.created_at.strftime('%Y-%m-%d'))
                for p in payments
            ),
        )
        from django.utils.safestring import mark_safe
        return mark_safe(
            '<table style="width:100%">'
            '<tr><th>دوره</th><th>مبلغ</th><th>وضعیت</th><th>تاریخ</th></tr>'
            f'{rows}</table>'
        )

    @admin.action(description='خروجی CSV')
    def export_users_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['mobile', 'first_name', 'last_name', 'national_code', 'is_active', 'date_joined'])
        for user in queryset:
            writer.writerow([
                user.mobile, user.first_name, user.last_name,
                user.national_code, user.is_active, user.date_joined,
            ])
        return response
