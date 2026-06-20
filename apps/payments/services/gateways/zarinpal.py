import logging

import requests
from django.conf import settings

from apps.payments.services.gateways.base import (
    BasePaymentGateway,
    PaymentRequestResult,
    PaymentVerifyResult,
)

logger = logging.getLogger(__name__)


class ZarinpalGateway(BasePaymentGateway):
    SANDBOX_REQUEST_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
    SANDBOX_VERIFY_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
    SANDBOX_START_PAY_URL = 'https://sandbox.zarinpal.com/pg/StartPay/'

    PRODUCTION_REQUEST_URL = 'https://api.zarinpal.com/pg/v4/payment/request.json'
    PRODUCTION_VERIFY_URL = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
    PRODUCTION_START_PAY_URL = 'https://www.zarinpal.com/pg/StartPay/'

    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.sandbox = settings.ZARINPAL_SANDBOX

    @property
    def request_url(self):
        return self.SANDBOX_REQUEST_URL if self.sandbox else self.PRODUCTION_REQUEST_URL

    @property
    def verify_url(self):
        return self.SANDBOX_VERIFY_URL if self.sandbox else self.PRODUCTION_VERIFY_URL

    @property
    def start_pay_url(self):
        return self.SANDBOX_START_PAY_URL if self.sandbox else self.PRODUCTION_START_PAY_URL

    def request_payment(self, amount: int, description: str, callback_url: str, mobile: str = '') -> PaymentRequestResult:
        payload = {
            'merchant_id': self.merchant_id,
            'amount': amount,
            'description': description,
            'callback_url': callback_url,
        }
        if mobile:
            payload['metadata'] = {'mobile': mobile}

        response = requests.post(self.request_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get('data') and data['data'].get('code') == 100:
            authority = data['data']['authority']
            return PaymentRequestResult(
                authority=authority,
                payment_url=f'{self.start_pay_url}{authority}',
            )

        errors = data.get('errors', {})
        message = errors.get('message', 'خطا در ایجاد درخواست پرداخت')
        raise ValueError(message)

    def verify_payment(self, authority: str, amount: int) -> PaymentVerifyResult:
        payload = {
            'merchant_id': self.merchant_id,
            'amount': amount,
            'authority': authority,
        }

        response = requests.post(self.verify_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get('data') and data['data'].get('code') in (100, 101):
            return PaymentVerifyResult(
                success=True,
                ref_id=str(data['data'].get('ref_id', '')),
                message='پرداخت با موفقیت انجام شد.',
            )

        errors = data.get('errors', {})
        return PaymentVerifyResult(
            success=False,
            message=errors.get('message', 'پرداخت ناموفق بود.'),
        )
