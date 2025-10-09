import os, stripe
from typing import Dict, Optional

class StripeGateway:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not self.api_key:
            raise RuntimeError("STRIPE_API_KEY not set")
        stripe.api_key = self.api_key

    def create_checkout(self, amount_cents: int, currency: str, order_id: str, title: str, email: Optional[str] = None) -> str:
        success_url = os.getenv("PAY_SUCCESS_URL")
        cancel_url = os.getenv("PAY_CANCEL_URL")
        if not success_url or not cancel_url:
            raise RuntimeError("PAY_SUCCESS_URL/PAY_CANCEL_URL not set")
        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=f"{success_url}?order_id={order_id}",
            cancel_url=f"{cancel_url}?order_id={order_id}",
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": title},
                    "unit_amount": amount_cents,
                },
                "quantity": 1
            }],
            customer_email=email,
            metadata={"order_id": order_id, "title": title}
        )
        return session.url

    def parse_webhook(self, payload: bytes, sig_header: str):
        if not self.webhook_secret:
            raise RuntimeError("STRIPE_WEBHOOK_SECRET not set")
        return stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)

    @staticmethod
    def extract_success(event) -> Optional[Dict]:
        et = event.get("type")
        obj = event.get("data", {}).get("object", {})
        if et == "checkout.session.completed":
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
