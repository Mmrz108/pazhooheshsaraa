import csv

from django.contrib import admin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from apps.courses.models import Course, CourseCategory, Enrollment, EnrollmentStatus


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active', 'course_count_display']
    list_filter = ['is_active']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['order', 'is_active']
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'description', 'order', 'is_active')}),
        ('SEO', {'fields': ('meta_title', 'meta_description')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _course_count=Count('courses', filter=Q(courses__is_active=True)),
        )

    @admin.display(description='تعداد دوره')
    def course_count_display(self, obj):
        return obj._course_count


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ['user', 'payment', 'enrollment_date', 'status']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'price', 'age_group', 'level', 'capacity',
        'enrolled_count_display', 'total_revenue_display',
        'start_date', 'is_active',
    ]
    list_filter = ['is_active', 'category', 'age_group', 'level', 'start_date']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'enrollment_stats']
    inlines = [EnrollmentInline]
    actions = ['export_courses_csv']
    autocomplete_fields = ['category']

    fieldsets = (
        (None, {'fields': ('title', 'slug', 'category', 'description', 'image')}),
        ('جزئیات', {'fields': ('price', 'age_group', 'level', 'capacity', 'start_date', 'end_date')}),
        ('آمار', {'fields': ('enrollment_stats',)}),
        ('وضعیت', {'fields': ('is_active', 'created_at')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _enrolled_count=Count(
                'enrollments',
                filter=Q(enrollments__status=EnrollmentStatus.PAID),
            ),
            _total_revenue=Sum(
                'enrollments__payment__amount',
                filter=Q(enrollments__status=EnrollmentStatus.PAID),
            ),
        )

    @admin.display(description='تعداد دانش‌آموز')
    def enrolled_count_display(self, obj):
        return obj._enrolled_count

    @admin.display(description='درآمد کل')
    def total_revenue_display(self, obj):
        return f'{(obj._total_revenue or 0):,} تومان'

    @admin.display(description='آمار ثبت‌نام')
    def enrollment_stats(self, obj):
        if not obj.pk:
            return '-'
        stats = obj.enrollments.values('status').annotate(count=Count('id'))
        rows = format_html_join(
            '', '<tr><td>{}</td><td>{}</td></tr>',
            ((s['status'], s['count']) for s in stats),
        )
        return mark_safe(
            f'<table><tr><th>وضعیت</th><th>تعداد</th></tr>{rows}</table>'
            f'<p>ظرفیت باقیمانده: {obj.remaining_capacity}</p>'
        )

    @admin.action(description='خروجی CSV')
    def export_courses_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="courses.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['title', 'slug', 'category', 'price', 'capacity', 'start_date', 'end_date', 'is_active'])
        for course in queryset.select_related('category'):
            writer.writerow([
                course.title, course.slug, course.category.title, course.price, course.capacity,
                course.start_date, course.end_date, course.is_active,
            ])
        return response


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'status', 'payment_status_display', 'enrollment_date']
    list_filter = ['status', 'enrollment_date', 'course']
    search_fields = ['user__mobile', 'user__first_name', 'user__last_name', 'course__title']
    readonly_fields = ['enrollment_date']
    autocomplete_fields = ['user', 'course', 'payment']
    actions = ['export_enrollments_csv']

    @admin.display(description='وضعیت پرداخت')
    def payment_status_display(self, obj):
        if obj.payment:
            return obj.payment.get_status_display()
        return '-'

    @admin.action(description='خروجی CSV')
    def export_enrollments_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="enrollments.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['user', 'course', 'status', 'payment_status', 'enrollment_date'])
        for e in queryset.select_related('user', 'course', 'payment'):
            writer.writerow([
                e.user.mobile, e.course.title, e.status,
                e.payment.status if e.payment else '',
                e.enrollment_date,
            ])
        return response
