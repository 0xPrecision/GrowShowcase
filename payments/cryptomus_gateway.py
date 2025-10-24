import os, json, base64, hashlib, httpx
from typing import Dict, Optional
from dotenv import load_dotenv

from web.main_helpers import make_urls

load_dotenv()


class CryptomusGateway:
    def __init__(self):
        self.merchant_id = os.getenv("CRYPTOMUS_MERCHANT_ID")
        self.api_key = os.getenv("CRYPTOMUS_API_KEY")
        self.base_url = (os.getenv("CRYPTOMUS_BASE_URL")).rstrip("/")
        if not self.merchant_id or not self.api_key:
            raise RuntimeError("CRYPTOMUS creds not set")
        # Рекомендуется переиспользовать клиент
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=20)

    # Правильная подпись: md5( base64(json_body) + API_KEY)
    def _sign(self, body_bytes: bytes) -> str:
        b64 = base64.b64encode(body_bytes).decode()
        return hashlib.md5((b64 + self.api_key).encode()).hexdigest()

    async def create_invoice(
        self,
        amount: str,
        currency: str,
        order_id: str,
        title: Optional[str] = None,
        to_currency: Optional[str] = None,  # например "USDT"
        network: Optional[str] = None,  # например "tron"
        url_callback: Optional[str] = None,
        lifetime: int = 3600,
        subtract: Optional[int] = 0,  # 0..100 — процент комиссии на клиента
        additional_data: Optional[str] = None,
    ) -> Dict[str, str]:
        # Собираем тело по их названиям полей
        success_url, cancel_url = make_urls(order_uid=order_id)
        payload: Dict[str, object] = {
            "amount": str(amount),
            "currency": currency.upper(),
            "order_id": order_id,
            "description": title,
            "to_currency": to_currency,
            "network": network,  # для инвойса сеть указывается строчно ("tron")
            "url_success": success_url,
            "url_return": cancel_url,
            "url_callback": url_callback,
            "lifetime": lifetime,
            "subtract": subtract,
            "additional_data": additional_data,
        }
        # выкинем None
        payload = {k: v for k, v in payload.items() if v is not None}

        # ТЕЛО сериализуем сами и используем ОДИНАКОВЫЕ байты и для подписи, и для запроса
        body_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        body_bytes = body_str.encode("utf-8")

        headers = {
            "merchant": self.merchant_id,  # именно merchant для Merchant API
            "sign": self._sign(body_bytes),  # md5(base64(body)+API_KEY)
            "Content-Type": "application/json",
        }

        r = await self.client.post("/v1/payment", headers=headers, content=body_bytes)
        r.raise_for_status()
        data = r.json()

        # Ответ у них идёт в result
        result = data.get("result") or {}
        url = result.get("url") or data.get("url")
        uuid = result.get("uuid") or data.get("uuid")
        if not url:
            raise RuntimeError(f"Cryptomus invoice: no url in {data}")
        return {"url": url, "uuid": str(uuid) if uuid else ""}

    # Верификация вебхука: md5( base64(raw_body) + API_KEY ), sign приходит в заголовке
    def verify_webhook(self, raw: bytes, signature: str) -> Dict:
        expected = hashlib.md5(
            (base64.b64encode(raw).decode() + self.api_key).encode()
        ).hexdigest()
        if (signature or "").lower() != expected:
            raise ValueError("Invalid signature")
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def extract_success(payload: Dict) -> Optional[Dict]:
        status = (payload.get("status") or "").lower()
        # успех — только paid / paid_over
        if status in ("paid", "paid_over"):
            return {
                "order_id": payload.get("order_id") or payload.get("merchant_order_id"),
                "amount": payload.get("amount"),
                "currency": (payload.get("currency") or "").upper(),
                "txid": payload.get("txid") or payload.get("hash"),
                "uuid": payload.get("uuid"),
                "status": status,
            }
        # отмена/фейл обрабатываются в контроллере вебхука
        return None
