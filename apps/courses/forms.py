from django import forms
from django.core.exceptions import ValidationError
import jdatetime

from apps.courses.models import Course
from common.jalali import format_jalali_date, parse_jalali_date


def _jalali_sample():
    today = jdatetime.date.today()
    return f'{today.year}/{today.month:02d}/{today.day:02d}'


def _jalali_date_widget():
    sample = _jalali_sample()
    return forms.TextInput(
        attrs={
            'placeholder': sample,
            'dir': 'ltr',
            'class': 'vTextField',
            'inputmode': 'numeric',
        },
    )


def _shamsi_date_field(label, *, required=False, help_text=''):
    sample = _jalali_sample()
    return forms.CharField(
        label=label,
        required=required,
        widget=_jalali_date_widget(),
        help_text=help_text or f'مثال: {sample}',
    )


class CourseAdminForm(forms.ModelForm):
    start_date_shamsi = _shamsi_date_field('تاریخ شروع (شمسی)', required=True)
    end_date_shamsi = _shamsi_date_field('تاریخ پایان (شمسی)', required=True)
    registration_deadline_shamsi = _shamsi_date_field(
        'فرصت ثبت‌نام تا (شمسی)',
        required=True,
        help_text='پس از این تاریخ دکمه ثبت‌نام غیرفعال می‌شود. سال شمسی جاری را وارد کنید.',
    )

    class Meta:
        model = Course
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('start_date', 'end_date', 'registration_deadline'):
            self.fields.pop(name, None)

        if self.instance.pk:
            if self.instance.start_date:
                self.fields['start_date_shamsi'].initial = format_jalali_date(self.instance.start_date)
            if self.instance.end_date:
                self.fields['end_date_shamsi'].initial = format_jalali_date(self.instance.end_date)
            if self.instance.registration_deadline:
                self.fields['registration_deadline_shamsi'].initial = format_jalali_date(
                    self.instance.registration_deadline,
                )

    def _parse_shamsi(self, value, *, required=False):
        if not value:
            if required:
                raise ValidationError('این فیلد الزامی است.')
            return None
        try:
            return parse_jalali_date(value)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def clean_start_date_shamsi(self):
        return self._parse_shamsi(self.cleaned_data.get('start_date_shamsi', ''), required=True)

    def clean_end_date_shamsi(self):
        return self._parse_shamsi(self.cleaned_data.get('end_date_shamsi', ''), required=True)

    def clean_registration_deadline_shamsi(self):
        return self._parse_shamsi(
            self.cleaned_data.get('registration_deadline_shamsi', ''),
            required=True,
        )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date_shamsi')
        end = cleaned.get('end_date_shamsi')
        deadline = cleaned.get('registration_deadline_shamsi')
        if start and end and end < start:
            raise ValidationError({'end_date_shamsi': 'تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.'})
        if deadline and end and deadline > end:
            raise ValidationError({
                'registration_deadline_shamsi': 'فرصت ثبت‌نام نمی‌تواند بعد از تاریخ پایان دوره باشد.',
            })
        return cleaned

    def save(self, commit=True):
        course = super().save(commit=False)
        course.start_date = self.cleaned_data['start_date_shamsi']
        course.end_date = self.cleaned_data['end_date_shamsi']
        course.registration_deadline = self.cleaned_data['registration_deadline_shamsi']
        if commit:
            course.save()
            self.save_m2m()
        return course
