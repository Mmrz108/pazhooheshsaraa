import csv

from django.http import HttpResponse


def export_as_csv(modeladmin, request, queryset, fields, filename):
    """Generic CSV export action for Django admin."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(fields)

    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field, '')
            if hasattr(value, '__call__'):
                value = value()
            row.append(str(value) if value is not None else '')
        writer.writerow(row)

    return response
