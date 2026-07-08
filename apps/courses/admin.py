import csv
from urllib.parse import quote

from django.contrib import admin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from apps.courses.availability import open_for_registration_q, visible_on_site_q
from apps.courses.forms import CourseAdminForm
from apps.courses.models import Course, CourseCategory, Enrollment, EnrollmentStatus
from apps.courses.services.enrollment_pdf import build_course_enrollments_pdf
from common.jalali import format_jalali_date

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
            _course_count=Count('courses', filter=visible_on_site_q(prefix='courses')),
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
    form = CourseAdminForm
    list_display = [
        'title', 'category', 'priority', 'price', 'age_group', 'level', 'capacity',
        'enrolled_count_display', 'total_revenue_display',
        'start_date_jalali', 'end_date_jalali', 'registration_deadline_jalali',
        'registration_status_display', 'is_active',
    ]
    list_filter = ['is_active', 'category', 'age_group', 'level', 'start_date']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'enrollment_stats']
    inlines = [EnrollmentInline]
    actions = ['export_courses_csv']
    list_editable = ['priority']

    fieldsets = (
        (None, {'fields': ('title', 'slug', 'category', 'description', 'image')}),
        ('جزئیات', {
            'fields': (
                'price', 'age_group', 'level', 'capacity',
                'start_date_shamsi', 'end_date_shamsi', 'registration_deadline_shamsi',
                'schedule',
            ),
        }),
        ('آمار', {'fields': ('enrollment_stats',)}),
        ('وضعیت', {'fields': ('priority', 'is_active', 'created_at')}),
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

    @admin.display(description='تاریخ شروع', ordering='start_date')
    def start_date_jalali(self, obj):
        return format_jalali_date(obj.start_date)

    @admin.display(description='تاریخ پایان', ordering='end_date')
    def end_date_jalali(self, obj):
        return format_jalali_date(obj.end_date)

    @admin.display(description='فرصت ثبت‌نام تا', ordering='registration_deadline')
    def registration_deadline_jalali(self, obj):
        return format_jalali_date(obj.registration_deadline)

    @admin.display(description='وضعیت ثبت‌نام', boolean=True)
    def registration_status_display(self, obj):
        return obj.is_registration_open

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
    list_display = ['user_link', 'course', 'status', 'payment_status_display', 'enrollment_date']
    list_filter = ['status', 'enrollment_date', 'course']
    search_fields = ['user__mobile', 'user__first_name', 'user__last_name', 'course__title']
    readonly_fields = ['enrollment_date']
    autocomplete_fields = ['user', 'course', 'payment']
    actions = ['export_enrollments_csv']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'course/<int:course_id>/',
                self.admin_site.admin_view(self.course_enrollments_view),
                name='courses_enrollment_by_course',
            ),
            path(
                'course/<int:course_id>/export-pdf/',
                self.admin_site.admin_view(self.export_course_enrollments_pdf),
                name='courses_enrollment_export_pdf',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        courses = (
            Course.objects.select_related('category')
            .annotate(
                total_enrollments=Count('enrollments'),
                paid_enrollments=Count(
                    'enrollments',
                    filter=Q(enrollments__status=EnrollmentStatus.PAID),
                ),
            )
            .order_by('-created_at')
        )
        context = {
            **self.admin_site.each_context(request),
            'title': 'ثبت\u200cنام\u200cها — انتخاب دوره',
            'courses': courses,
            'opts': self.model._meta,
            'cl': None,
            'media': self.media,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_view_permission': self.has_view_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
        }
        return TemplateResponse(request, 'admin/courses/enrollment/course_list.html', context)

    def course_enrollments_view(self, request, course_id):
        course = get_object_or_404(Course.objects.select_related('category'), pk=course_id)
        enrollments = (
            Enrollment.objects.filter(course=course)
            .select_related('user', 'payment')
            .order_by('-enrollment_date')
        )
        context = {
            **self.admin_site.each_context(request),
            'title': f'ثبت\u200cنام\u200cهای {course.title}',
            'course': course,
            'enrollments': enrollments,
            'opts': self.model._meta,
            'cl': None,
            'media': self.media,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_view_permission': self.has_view_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
        }
        return TemplateResponse(request, 'admin/courses/enrollment/course_enrollments.html', context)

    def export_course_enrollments_pdf(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        enrollments = (
            Enrollment.objects.filter(course=course)
            .select_related('user', 'payment')
            .order_by('user__last_name', 'user__first_name')
        )
        pdf_buffer = build_course_enrollments_pdf(course, enrollments)
        filename = f'enrollments-{course.slug or course.pk}.pdf'
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
        return response

    @admin.display(description='دانش\u200cآموز', ordering='user__last_name')
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)

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