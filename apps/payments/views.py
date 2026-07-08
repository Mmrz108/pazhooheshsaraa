from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.availability import open_for_registration_q
from apps.courses.models import Course
from apps.payments.models import Payment, PaymentStatus
from apps.payments.serializers import StartPaymentSerializer
from apps.payments.services.payment_service import PaymentService, PaymentServiceError


def _payment_redirect_url(success: bool, **params) -> str:
    base = settings.PAYMENT_SUCCESS_REDIRECT_URL if success else settings.PAYMENT_FAILED_REDIRECT_URL
    if not params:
        return base
    separator = '&' if '?' in base else '?'
    return f'{base}{separator}{urlencode(params)}'


class StartPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StartPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            course = Course.objects.filter(open_for_registration_q()).get(
                id=serializer.validated_data['course_id'],
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


@method_decorator(csrf_exempt, name='dispatch')
class VerifyPaymentView(APIView):
    permission_classes = [AllowAny]

    def _verify_response(self, request, authority: str, status_param: str = 'OK'):
        try:
            result = PaymentService().verify_payment(authority, status_param)
        except PaymentServiceError as e:
            if settings.PAYMENT_DIRECT_REDIRECT and request.method == 'POST':
                return HttpResponseRedirect(
                    _payment_redirect_url(False, code=e.code, message=e.message),
                )
            return Response({'detail': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)

        if settings.PAYMENT_DIRECT_REDIRECT and request.method == 'POST':
            return HttpResponseRedirect(
                _payment_redirect_url(
                    True,
                    ref_id=result.get('ref_id', ''),
                    course=result.get('course', ''),
                ),
            )
        return Response(result, status=status.HTTP_200_OK)

    def get(self, request):
        authority = request.query_params.get('Authority', '')
        status_param = request.query_params.get('Status', '')

        if not authority:
            return Response(
                {'detail': 'Authority الزامی است.', 'code': 'missing_authority'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._verify_response(request, authority, status_param)

    def post(self, request):
        token = request.data.get('token') or request.data.get('Token', '')
        res_code = str(request.data.get('rescode') or request.data.get('ResCode', ''))
        order_id = request.data.get('orderid') or request.data.get('OrderId')

        if not token and order_id:
            payment = Payment.objects.filter(id=order_id).first()
            if payment:
                token = payment.authority

        if not token:
            if settings.PAYMENT_DIRECT_REDIRECT:
                return HttpResponseRedirect(
                    _payment_redirect_url(False, code='missing_token', message='توکن پرداخت یافت نشد.'),
                )
            return Response(
                {'detail': 'توکن پرداخت الزامی است.', 'code': 'missing_token'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if res_code and res_code != '0':
            payment = Payment.objects.filter(authority=token).first()
            if payment and payment.status == PaymentStatus.PENDING:
                payment.status = PaymentStatus.FAILED
                payment.save(update_fields=['status'])
            if settings.PAYMENT_DIRECT_REDIRECT:
                return HttpResponseRedirect(
                    _payment_redirect_url(False, code='cancelled', message='پرداخت توسط کاربر لغو شد.'),
                )
            return Response(
                {'detail': 'پرداخت توسط کاربر لغو شد.', 'code': 'cancelled'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._verify_response(request, token, 'OK')
