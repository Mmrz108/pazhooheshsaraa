from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course
from apps.payments.serializers import StartPaymentSerializer
from apps.payments.services.payment_service import PaymentService, PaymentServiceError


class StartPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StartPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            course = Course.objects.get(
                id=serializer.validated_data['course_id'],
                is_active=True,
            )
        except Course.DoesNotExist:
            return Response(
                {'detail': 'دوره یافت نشد.', 'code': 'course_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            result = PaymentService().start_payment(request.user, course)
        except PaymentServiceError as e:
            return Response({'detail': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_201_CREATED)


class VerifyPaymentView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        authority = request.query_params.get('Authority', '')
        status_param = request.query_params.get('Status', '')

        if not authority:
            return Response(
                {'detail': 'Authority الزامی است.', 'code': 'missing_authority'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = PaymentService().verify_payment(authority, status_param)
        except PaymentServiceError as e:
            return Response({'detail': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
