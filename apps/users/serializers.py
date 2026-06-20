from rest_framework import serializers

from common.validators import (
    normalize_digits,
    normalize_mobile,
    validate_iranian_mobile,
    validate_iranian_national_code,
)


class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)

    def validate_mobile(self, value):
        value = normalize_mobile(value)
        validate_iranian_mobile(value)
        return value


class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_mobile(self, value):
        return normalize_mobile(value)

    def validate_code(self, value):
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        normalized = str(value).strip()
        for index, digit in enumerate(persian_digits):
            normalized = normalized.replace(digit, str(index))
        if not normalized.isdigit() or len(normalized) != 6:
            raise serializers.ValidationError('کد تأیید باید ۶ رقم باشد.')
        return normalized


class ResendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)

    def validate_mobile(self, value):
        return normalize_mobile(value)


class CompleteRegistrationSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    national_code = serializers.CharField(max_length=10)
    father_name = serializers.CharField(max_length=150)
    birth_date = serializers.DateField()

    def validate_mobile(self, value):
        return normalize_mobile(value)

    def validate_national_code(self, value):
        value = normalize_digits(value)
        validate_iranian_national_code(value)
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class AdminAccessSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class UserAuthSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        from apps.users.models import User

        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'national_code', 'mobile', 'father_name', 'birth_date', 'date_joined',
            'is_staff',
        ]


class UserProfileSerializer(UserAuthSerializer):
    class Meta(UserAuthSerializer.Meta):
        pass


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.users.models import User

        model = User
        fields = ['first_name', 'last_name', 'father_name', 'birth_date']
