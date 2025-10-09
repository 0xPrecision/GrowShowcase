from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from contextlib import asynccontextmanager

from database.init_db import init_db, close_db
from database.models import Order
from payments.cryptomus_gateway import CryptomusGateway
from payments.stripe_gateway import StripeGateway


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()      # миграции/инициализация соединений
    try:
        yield
    finally:
        await close_db() # аккуратно закрыть коннекты


app = FastAPI(title="ShopBot Webhooks", lifespan=lifespan)


@app.get("/health")
async def health():
    return PlainTextResponse("ok")

@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    gw = StripeGateway()
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature","")
    try:
        event = gw.parse_webhook(payload, sig)
    except Exception as e:
        raise HTTPException(400, str(e))
    data = StripeGateway.extract_success(event)
    if data and data.get("order_id"):
        order = await Order.get_or_none(order_uid=data["order_id"])
        if order:
            order.status = "paid"
            order.provider = "stripe"
            order.amount_cents = data.get("amount_cents") or order.amount_cents
            order.currency = data.get("currency") or order.currency
            await order.save()
    return JSONResponse({"ok": True})

@app.post("/webhook/cryptomus")
async def webhook_cryptomus(request: Request):
    gw = CryptomusGateway()
    raw = await request.body()
    signature = request.headers.get("sign") or request.headers.get("Sign") or ""
    try:
        body = gw.verify_webhook(raw, signature)
    except Exception as e:
        raise HTTPException(400, f"bad signature: {e}")
    data = CryptomusGateway.extract_success(body)
    if data and data.get("order_id"):
        order = await Order.get_or_none(order_uid=data["order_id"])
        if order:
            order.status = "paid"
            order.provider = "cryptomus"
            order.txid = data.get("txid")
            await order.save()
    return JSONResponse({"ok": True})
