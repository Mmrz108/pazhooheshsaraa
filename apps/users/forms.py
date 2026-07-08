from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.users.models import User
from common.jalali import format_jalali_date, parse_jalali_date

BIRTH_DATE_WIDGET = forms.TextInput(
    attrs={
        'placeholder': '1385/03/15',
        'dir': 'ltr',
        'class': 'vTextField',
        'inputmode': 'numeric',
    },
)


class UserChangeAdminForm(UserChangeForm):
    birth_date_shamsi = forms.CharField(
        label='تاریخ تولد (شمسی)',
        required=False,
        widget=BIRTH_DATE_WIDGET,
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('birth_date', None)
        if self.instance.pk and self.instance.birth_date:
            self.fields['birth_date_shamsi'].initial = format_jalali_date(self.instance.birth_date)

    def save(self, commit=True):
        user = super().save(commit=False)
        raw = self.cleaned_data.get('birth_date_shamsi', '')
        user.birth_date = parse_jalali_date(raw) if raw else None
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserAddAdminForm(UserCreationForm):
    birth_date_shamsi = forms.CharField(
        label='تاریخ تولد (شمسی)',
        required=False,
        widget=BIRTH_DATE_WIDGET,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('mobile', 'first_name', 'last_name', 'national_code', 'father_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        raw = self.cleaned_data.get('birth_date_shamsi', '')
        user.birth_date = parse_jalali_date(raw) if raw else None
        if commit:
            user.save()
        return user
