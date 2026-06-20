from django.conf import settings
from django.db import transaction

from apps.courses.models import Enrollment, EnrollmentStatus
from apps.payments.models import Payment, PaymentGateway, PaymentStatus
from apps.payments.services.gateways.base import BasePaymentGateway
from apps.payments.services.gateways.zarinpal import ZarinpalGateway


class PaymentServiceError(Exception):
    def __init__(self, message, code='payment_error'):
        self.message = message
        self.code = code
        super().__init__(message)


class PaymentService:
    GATEWAYS: dict[str, type[BasePaymentGateway]] = {
        PaymentGateway.ZARINPAL: ZarinpalGateway,
    }

    def __init__(self, gateway: str = PaymentGateway.ZARINPAL):
        gateway_class = self.GATEWAYS.get(gateway)
        if not gateway_class:
            raise PaymentServiceError('درگاه پرداخت پشتیبانی نمی‌شود.', code='unsupported_gateway')
        self.gateway_name = gateway
        self.gateway = gateway_class()

    def start_payment(self, user, course) -> dict:
        if not course.is_active:
            raise PaymentServiceError('این دوره فعال نیست.', code='course_inactive')

        if course.is_full:
            raise PaymentServiceError('ظرفیت این دوره تکمیل شده است.', code='course_full')

        if Enrollment.objects.filter(
            user=user, course=course, status=EnrollmentStatus.PAID,
        ).exists():
            raise PaymentServiceError('شما قبلاً در این دوره ثبت‌نام کرده‌اید.', code='already_enrolled')

        pending = Payment.objects.filter(
            user=user, course=course, status=PaymentStatus.PENDING,
        ).first()
        if pending:
            pending.status = PaymentStatus.FAILED
            pending.save(update_fields=['status'])

        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=course.price,
            gateway=self.gateway_name,
            status=PaymentStatus.PENDING,
        )

        try:
            result = self.gateway.request_payment(
                amount=payment.amount,
                description=f'ثبت‌نام دوره {course.title}',
                callback_url=settings.PAYMENT_CALLBACK_URL,
                mobile=user.mobile,
            )
        except Exception as exc:
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=['status'])
            raise PaymentServiceError(
                f'خطا در اتصال به درگاه پرداخت: {exc}',
                code='gateway_error',
            ) from exc

        payment.authority = result.authority
        payment.save(update_fields=['authority'])

        return {
            'payment_id': payment.id,
            'authority': result.authority,
            'payment_url': result.payment_url,
            'amount': payment.amount,
        }

    @transaction.atomic
    def verify_payment(self, authority: str, status_param: str = 'OK') -> dict:
        if status_param != 'OK':
            payment = Payment.objects.filter(authority=authority).first()
            if payment:
                payment.status = PaymentStatus.FAILED
                payment.save(update_fields=['status'])
            raise PaymentServiceError('پرداخت توسط کاربر لغو شد.', code='cancelled')

        try:
            payment = Payment.objects.select_for_update().get(
                authority=authority,
                status=PaymentStatus.PENDING,
            )
        except Payment.DoesNotExist as exc:
            raise PaymentServiceError('تراکنش یافت نشد.', code='not_found') from exc

        try:
            result = self.gateway.verify_payment(authority, payment.amount)
        except Exception as exc:
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=['status'])
            raise PaymentServiceError(
                f'خطا در تأیید پرداخت: {exc}',
                code='verify_error',
            ) from exc

        if not result.success:
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=['status'])
            raise PaymentServiceError(result.message, code='verification_failed')

        payment.status = PaymentStatus.SUCCESSFUL
        payment.ref_id = result.ref_id
        payment.save(update_fields=['status', 'ref_id'])

        enrollment, created = Enrollment.objects.get_or_create(
            user=payment.user,
            course=payment.course,
            defaults={
                'payment': payment,
                'status': EnrollmentStatus.PAID,
            },
        )
        if not created:
            enrollment.payment = payment
            enrollment.status = EnrollmentStatus.PAID
            enrollment.save(update_fields=['payment', 'status'])

        return {
            'payment_id': payment.id,
            'ref_id': payment.ref_id,
            'course': payment.course.title,
            'amount': payment.amount,
            'enrollment_id': enrollment.id,
            'message': result.message,
        }
