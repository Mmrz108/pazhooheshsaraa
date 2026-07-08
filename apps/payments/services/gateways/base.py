from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PaymentRequestResult:
    authority: str
    payment_url: str


@dataclass
class PaymentVerifyResult:
    success: bool
    ref_id: str = ''
    message: str = ''


class BasePaymentGateway(ABC):
    @abstractmethod
    def request_payment(
        self,
        amount: int,
        description: str,
        callback_url: str,
        mobile: str = '',
        order_id: int | None = None,
    ) -> PaymentRequestResult:
        pass

    @abstractmethod
    def verify_payment(self, authority: str, amount: int) -> PaymentVerifyResult:
        pass
