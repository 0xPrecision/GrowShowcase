import os, json, hmac, hashlib, httpx
from typing import Dict, Optional

class CryptomusGateway:
    def __init__(self):
        self.merchant_id = os.getenv("CRYPTOMUS_MERCHANT_ID")
        self.api_key = os.getenv("CRYPTOMUS_API_KEY")
        self.base_url = (os.getenv("CRYPTOMUS_BASE_URL") or "https://api.cryptomus.com").rstrip("/")
        if not self.merchant_id or not self.api_key:
            raise RuntimeError("CRYPTOMUS creds not set")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=20)

    def _sign(self, payload: Dict) -> str:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
        return hmac.new(self.api_key.encode(), body, hashlib.sha256).hexdigest()

    async def create_invoice(self, amount: str, currency: str, order_id: str, network: Optional[str], title: str, callback_url: str, success_url: str) -> str:
        payload = {
            "merchant": self.merchant_id,
            "amount": str(amount),
            "currency": currency.upper(),
            "order_id": order_id,
            "network": network,          # 'TRC20' желательно
            "success_url": success_url,
            "callback_url": callback_url,
            "lifetime": 3600,
            "description": title
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        headers = {"merchant": self.merchant_id, "sign": self._sign(payload), "Content-Type": "application/json"}
        r = await self.client.post("/v1/payment", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        url = (data.get("result") or {}).get("url") or data.get("url")
        if not url:
            raise RuntimeError(f"Cryptomus invoice: no url in {data}")
        return url

    def verify_webhook(self, raw: bytes, signature: str) -> Dict:
        expected = hmac.new(self.api_key.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, (signature or "").lower()):
            raise ValueError("Invalid signature")
        return json.loads(raw.decode())

    @staticmethod
    def extract_success(payload: Dict) -> Optional[Dict]:
        status = (payload.get("status") or "").lower()
        if status in ("paid", "success", "confirm_check"):
            return {
                "order_id": payload.get("order_id") or payload.get("merchant_order_id"),
                "amount": payload.get("amount"),
                "currency": (payload.get("currency") or "").upper(),
                "txid": payload.get("txid") or payload.get("hash")
            }
        return None
