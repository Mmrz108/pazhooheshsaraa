import base64
import logging
from datetime import datetime

import requests
from Crypto.Cipher import DES3
from django.conf import settings

from apps.payments.services.gateways.base import (
    BasePaymentGateway,
    PaymentRequestResult,
    PaymentVerifyResult,
)

logger = logging.getLogger(__name__)


class SadadMelliGateway(BasePaymentGateway):
    REQUEST_URL = 'https://sadad.shaparak.ir/vpg/api/v0/Request/PaymentRequest'
    VERIFY_URL = 'https://sadad.shaparak.ir/vpg/api/v0/Advice/Verify'
    PURCHASE_URL = 'https://sadad.shaparak.ir/VPG/Purchase'

    def __init__(self):
        self.merchant_id = settings.SADAD_MERCHANT_ID
        self.terminal_id = settings.SADAD_TERMINAL_ID
        self.terminal_key = settings.SADAD_TERMINAL_KEY

    @staticmethod
    def _pad(text: str, pad_size: int = 8) -> str:
        text_length = len(text)
        remaining_space = pad_size - (text_length % pad_size)
        return text + (remaining_space * chr(remaining_space))

    def _encrypt_sign(self, text: str) -> str:
        secret_key_bytes = base64.b64decode(self.terminal_key)
        padded = self._pad(text, 8)
        cipher = DES3.new(secret_key_bytes, DES3.MODE_ECB)
        cipher_text = cipher.encrypt(padded.encode('utf-8'))
        return base64.b64encode(cipher_text).decode('utf-8')

    def _gateway_amount(self, amount_toman: int) -> int:
        return amount_toman * 10

    def request_payment(
        self,
        amount: int,
        description: str,
        callback_url: str,
        mobile: str = '',
        order_id: int | None = None,
    ) -> PaymentRequestResult:
        if not order_id:
            raise ValueError('OrderId برای درگاه سداد الزامی است.')

        gateway_amount = self._gateway_amount(amount)
        sign_data = self._encrypt_sign(f'{self.terminal_id};{order_id};{gateway_amount}')

        payload = {
            'TerminalId': self.terminal_id,
            'MerchantId': self.merchant_id,
            'Amount': gateway_amount,
            'SignData': sign_data,
            'ReturnUrl': callback_url,
            'LocalDateTime': datetime.now().strftime('%m/%d/%Y %H:%M:%S %p'),
            'OrderId': order_id,
        }
        if mobile:
            payload['AdditionalData'] = f'oi:{order_id}-ou:{mobile}'

        response = requests.post(self.REQUEST_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if str(data.get('ResCode')) == '0' and data.get('Token'):
            token = data['Token']
            return PaymentRequestResult(
                authority=token,
                payment_url=f'{self.PURCHASE_URL}?Token={token}',
            )

        message = data.get('Description', 'خطا در ایجاد درخواست پرداخت')
        raise ValueError(message)

    def verify_payment(self, authority: str, amount: int) -> PaymentVerifyResult:
        sign_data = self._encrypt_sign(authority)
        payload = {
            'Token': authority,
            'SignData': sign_data,
        }

        response = requests.post(self.VERIFY_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if str(data.get('ResCode')) == '0':
            ref_id = str(data.get('RetrivalRefNo') or data.get('SystemTraceNo') or '')
            return PaymentVerifyResult(
                success=True,
                ref_id=ref_id,
                message='پرداخت با موفقیت انجام شد.',
            )

        return PaymentVerifyResult(
            success=False,
            message=data.get('Description', 'پرداخت ناموفق بود.'),
        )
