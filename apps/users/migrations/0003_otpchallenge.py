# Generated manually for OTPChallenge model

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_profile_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='OTPChallenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobile', models.CharField(db_index=True, max_length=11, unique=True, verbose_name='شماره موبایل')),
                ('code', models.CharField(max_length=6, verbose_name='کد OTP')),
                ('attempts', models.PositiveSmallIntegerField(default=0, verbose_name='تعداد تلاش')),
                ('expires_at', models.DateTimeField(verbose_name='انقضای کد')),
                ('verified_at', models.DateTimeField(blank=True, null=True, verbose_name='زمان تأیید')),
                ('send_count', models.PositiveSmallIntegerField(default=1, verbose_name='تعداد ارسال')),
                ('send_window_started', models.DateTimeField(default=django.utils.timezone.now, verbose_name='شروع پنجره ارسال')),
                ('last_sent_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='آخرین ارسال')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'چالش OTP',
                'verbose_name_plural': 'چالش\u200cهای OTP',
            },
        ),
    ]
