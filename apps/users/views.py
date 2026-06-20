from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
import secrets

from django.conf import settings

from common.admin_session import clear_admin_session, grant_admin_session

from apps.users.serializers import (
    AdminAccessSerializer,
    CompleteRegistrationSerializer,
    LogoutSerializer,
    ResendOTPSerializer,
    SendOTPSerializer,
    UserAuthSerializer,
    VerifyOTPSerializer,
)
from apps.users.services.otp import OTPError, OTPService


class OTPRateThrottle(AnonRateThrottle):
    scope = 'otp'


def build_auth_response(user, is_new_user=False, status_code=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(user)
    return Response({
        'user': UserAuthSerializer(user).data,
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        },
        'is_new_user': is_new_user,
    }, status=status_code)


class SendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = OTPService().send_otp(serializer.validated_data['mobile'])
        except OTPError as e:
            payload = {'detail': e.message, 'code': e.code}
            if e.code == 'resend_cooldown':
                cooldown = OTPService()._get_resend_cooldown(serializer.validated_data['mobile'])
                payload['cooldown'] = cooldown
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = OTPService().verify_otp(
                serializer.validated_data['mobile'],
                serializer.validated_data['code'],
            )
        except OTPError as e:
            return Response({'detail': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)

        clear_admin_session(request)

        if result['action'] == 'login':
            return build_auth_response(result['user'], is_new_user=False)

        return Response({
            'requires_registration': True,
            'mobile': result['mobile'],
            'message': 'لطفاً اطلاعات خود را تکمیل کنید.',
        }, status=status.HTTP_200_OK)


class CompleteRegistrationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = CompleteRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = OTPService().complete_registration(**serializer.validated_data)
        except OTPError as e:
            return Response({'detail': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)

        clear_admin_session(request)
        return build_auth_response(user, is_new_user=True, status_code=status.HTTP_201_CREATED)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = OTPService().resend_otp(serializer.validated_data['mobile'])
        except OTPError as e:
            payload = {'detail': e.message, 'code': e.code}
            if e.code == 'resend_cooldown':
                payload['cooldown'] = OTPService()._get_resend_cooldown(serializer.validated_data['mobile'])
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
        except Exception:
            return Response({'detail': 'توکن نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)

        clear_admin_session(request)
        return Response({'detail': 'با موفقیت خارج شدید.'}, status=status.HTTP_200_OK)


class ClearAdminSessionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        clear_admin_session(request)
        return Response({'detail': 'نشست مدیریت پاک شد.'})


class AdminAccessView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {'detail': 'فقط مدیران مجاز به ورود هستند.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']

        if not self._is_valid_admin_password(request.user, password):
            return Response(
                {'detail': 'رمز مدیریت وبسایت نادرست است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grant_admin_session(request, request.user)
        next_url = request.data.get('next') or '/admin/'
        if not str(next_url).startswith('/admin'):
            next_url = '/admin/'

        return Response({'redirect_url': next_url})

    @staticmethod
    def _is_valid_admin_password(user, password):
        password = (password or '').strip()
        site_password = (getattr(settings, 'ADMIN_SITE_PASSWORD', '') or '').strip()
        if site_password and secrets.compare_digest(password, site_password):
            return True
        if user.has_usable_password() and user.check_password(password):
            return True
        return False
