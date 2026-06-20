from django.urls import path

from apps.payments.views import StartPaymentView, VerifyPaymentView

urlpatterns = [
    path('start/', StartPaymentView.as_view(), name='payment-start'),
    path('verify/', VerifyPaymentView.as_view(), name='payment-verify'),
]
