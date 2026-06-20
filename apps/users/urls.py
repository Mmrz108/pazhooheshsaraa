from django.urls import path

from apps.users.views import (
    AdminAccessView,
    ClearAdminSessionView,
    CompleteRegistrationView,
    LogoutView,
    ResendOTPView,
    SendOTPView,
    VerifyOTPView,
)

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('complete-registration/', CompleteRegistrationView.as_view(), name='complete-registration'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('clear-admin-session/', ClearAdminSessionView.as_view(), name='clear-admin-session'),
    path('admin-access/', AdminAccessView.as_view(), name='admin-access'),
]
