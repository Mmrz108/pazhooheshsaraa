from rest_framework import serializers

from apps.payments.models import Payment


class StartPaymentSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'course', 'course_title', 'amount', 'authority',
            'ref_id', 'gateway', 'status', 'status_display', 'created_at',
        ]
        read_only_fields = fields
