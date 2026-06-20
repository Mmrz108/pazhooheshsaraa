import csv

from django.contrib import admin
from django.http import HttpResponse

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'course', 'amount', 'gateway', 'status', 'ref_id', 'created_at']
    list_filter = ['status', 'gateway', 'created_at']
    search_fields = ['user__mobile', 'user__first_name', 'authority', 'ref_id', 'course__title']
    readonly_fields = ['created_at', 'authority', 'ref_id']
    autocomplete_fields = ['user', 'course']
    actions = ['export_payments_csv']

    @admin.action(description='خروجی CSV')
    def export_payments_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="payments.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['user', 'course', 'amount', 'gateway', 'status', 'ref_id', 'created_at'])
        for p in queryset.select_related('user', 'course'):
            writer.writerow([
                p.user.mobile, p.course.title, p.amount,
                p.gateway, p.status, p.ref_id, p.created_at,
            ])
        return response
