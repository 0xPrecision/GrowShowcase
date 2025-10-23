import os
import stripe
from typing import Dict, Optional, List
from uuid import uuid4


class StripeGateway:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not self.api_key:
            raise RuntimeError("STRIPE_SECRET_KEY not set")
        stripe.api_key = self.api_key

    def _build_line_items(self, currency: str, items: List[Dict]) -> List[Dict]:
        """
        items: [{ 'title': str, 'unit_amount_cents': int, 'quantity': int }, ...]
        """
        li: List[Dict] = []
        ccy = currency.lower()
        for it in items:
            title = (it.get("title") or "Item")[:127]
            unit = int(it.get("unit_amount_cents") or 0)
            qty = int(it.get("quantity") or 0)
            if unit <= 0 or qty <= 0:
                # пропускаем мусор/ошибочные позиции
                continue
            li.append(
                {
                    "price_data": {
                        "currency": ccy,
                        "product_data": {"name": title},
                        "unit_amount": unit,
                    },
                    "quantity": qty,
                }
            )
        if not li:
            raise RuntimeError("Empty line_items after validation")
        return li

    @staticmethod
    def _sum_items_cents(items: List[Dict]) -> int:
        total = 0
        for it in items:
            unit = int(it.get("unit_amount_cents") or 0)
            qty = int(it.get("quantity") or 0)
            if unit > 0 and qty > 0:
                total += unit * qty
        return total

    def create_checkout(
        self,
        *,
        order_id: str,
        currency: str,
        # предпочтительный путь: детальные позиции
        items: Optional[List[Dict]] = None,
        # режим обратной совместимости: один агрегат
        amount_cents: Optional[int] = None,
        title: Optional[str] = None,
        email: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        locale: Optional[str] = None,
        # опциональное компактное мета: {'items_count':..., 'cart_hash':...}
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Создает Stripe Checkout Session с детальным чеком.
        Возвращает url/session_id/payment_intent/customer.
        """
        success_url = os.getenv("PAY_SUCCESS_URL")
        cancel_url = os.getenv("PAY_CANCEL_URL")
        if not success_url or not cancel_url:
            raise RuntimeError("PAY_SUCCESS_URL/PAY_CANCEL_URL not set")

        # line_items: либо из items, либо агрегат из amount_cents+title
        if items and len(items) > 0:
            line_items = self._build_line_items(currency, items)
            computed_total = self._sum_items_cents(items)
            if amount_cents is not None:
                # защита от рассинхрона total и позиций
                if int(amount_cents) != int(computed_total):
                    raise RuntimeError(
                        f"amount_cents mismatch: expected={amount_cents} computed={computed_total}"
                    )
            amount_cents = computed_total
            items_count = sum(
                int(it.get("quantity") or 0)
                for it in items
                if int(it.get("quantity") or 0) > 0
            )
        else:
            # агрегированный фоллбек
            if amount_cents is None or not title:
                raise RuntimeError(
                    "Either 'items' or ('amount_cents' and 'title') must be provided"
                )
            line_items = [
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": title[:127]},
                        "unit_amount": int(amount_cents),
                    },
                    "quantity": 1,
                }
            ]
            items_count = 1

        # idempotency для защиты от дублей
        idem = idempotency_key or f"checkout:{order_id}:{uuid4()}"

        # компактные метаданные
        md = {
            "order_id": order_id,
            "items_count": str(items_count),
        }
        if metadata:
            # вплавляем только компактные ключи-значения
            for k, v in metadata.items():
                if v is None:
                    continue
                v_str = str(v)
                if len(k) <= 40 and len(v_str) <= 500:
                    md[k] = v_str

        params = dict(
            mode="payment",
            success_url=f"{success_url}?order_id={order_id}",
            cancel_url=f"{cancel_url}?order_id={order_id}",
            line_items=line_items,
            customer_email=email,
            # клонируем в PI, чтобы ловить order_id и в payment_intent.succeeded
            payment_intent_data={"metadata": md},
            metadata=md,
        )
        if locale:
            params["locale"] = locale  # 'en' | 'ru' | 'auto' ...

        session: stripe.checkout.Session = stripe.checkout.Session.create(
            **params,
            idempotency_key=idem,
        )

        pi = session.get("payment_intent") or ""
        return {
            "url": session["url"],
            "session_id": session["id"],
            "payment_intent": pi if isinstance(pi, str) else str(pi),
            "customer": (
                (session.get("customer") or "")
                if isinstance(session.get("customer"), str)
                else ""
            ),
        }

    def parse_webhook(self, payload: bytes, sig_header: str):
        if not self.webhook_secret:
            raise RuntimeError("STRIPE_WEBHOOK_SECRET not set")
        return stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)

    @staticmethod
    def extract_success(event) -> Optional[Dict]:
        et = event.get("type")
        obj = event.get("data", {}).get("object", {}) or {}

        if et == "checkout.session.completed":
            if obj.get("payment_status") != "paid":
                return None
            md = obj.get("metadata") or {}
            return {
                "order_id": md.get("order_id"),
                "amount_cents": obj.get("amount_total"),
                "currency": (obj.get("currency") or "").upper(),
            }

        if et == "payment_intent.succeeded":
            md = obj.get("metadata") or {}
            return {
                "order_id": md.get("order_id"),
                "amount_cents": obj.get("amount"),
                "currency": (obj.get("currency") or "").upper(),
            }

        return None
