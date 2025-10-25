import asyncio
import os
import logging
from contextlib import asynccontextmanager
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse

from aiogram import Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.redis import RedisStorage


from database.init_db import init_db, close_db
from database.models import Order
from payments.stripe_gateway import StripeGateway
from web.main_helpers import (
    _tg_redirect_html,
    _notify_user_success,
    _verify,
    _notify_user_cancel,
)
from config_data.bot_instance import bot

from payments.cryptomus_gateway import CryptomusGateway

from services.i18n.middleware import LocaleMiddleware
from services.i18n.translations import Translator
from services.locale_repo import LocaleRepo


load_dotenv()

# -------------------------
# Logging
# -------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("web")

# -------------------------
# ENV
# -------------------------
BOT_USERNAME = os.getenv("BOT_USERNAME")
if not BOT_USERNAME:
    raise RuntimeError("BOT_USERNAME is not set")

WEBHOOK_BASE = os.getenv("TELEGRAM_WEBHOOK_URL")  # например: https://bot.example.com
if not WEBHOOK_BASE or not WEBHOOK_BASE.startswith(("https://", "http://")):
    raise RuntimeError(
        "TELEGRAM_WEBHOOK_URL must be an absolute URL with scheme (https://...)"
    )

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    # В проде секрет обязателен
    raise RuntimeError("TELEGRAM_WEBHOOK_SECRET is not set")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Секретный сегмент пути обязателен в проде
TELEGRAM_PATH_SEGMENT = WEBHOOK_SECRET
TELEGRAM_WEBHOOK_PATH = f"/webhook/telegram/{TELEGRAM_PATH_SEGMENT}"
TELEGRAM_WEBHOOK_URL = WEBHOOK_BASE.rstrip("/") + TELEGRAM_WEBHOOK_PATH

# -------------------------
# Bot / Dispatcher
# -------------------------
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)
log.info("REDIS_URL=%s", os.getenv("REDIS_URL"))

# i18n
translator = Translator(
    locales_dir=Path("locales").resolve(),
    default_locale="ru",
    supported=("ru", "en"),
)
locale_repo = LocaleRepo()
dp.update.middleware.register(LocaleMiddleware(translator, locale_repo))

# Роутеры
try:
    from handlers.admin_handlers import router as admin_router

    dp.include_router(admin_router)
except Exception as e:
    log.info("admin_handlers not loaded: %s", e)

try:
    from handlers.user_handlers import router as user_router

    dp.include_router(user_router)
except Exception as e:
    log.info("user_handlers not loaded: %s", e)


# -------------------------
# FastAPI app with lifespan
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация БД
    await init_db()

    # Установка вебхука (идемпотентно, просто перезапишет)
    try:
        await bot.set_webhook(
            url=TELEGRAM_WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET,  # Телега пришлет X-Telegram-Bot-Api-Secret-Token
            drop_pending_updates=True,
            allowed_updates=[
                "message",
                "edited_message",
                "callback_query",
                "chat_member",
                "my_chat_member",
            ],
        )
        log.info("Webhook set to %s", TELEGRAM_WEBHOOK_URL)
    except Exception as e:
        log.exception("Failed to set webhook: %s", e)
        raise

    try:
        yield
    finally:
        # В проде вебхук не удаляем, чтобы не бить трафик на рестартах
        try:
            await close_db()
        finally:
            try:
                await bot.session.close()
            except Exception:
                pass


app = FastAPI(title="ShopBot Webhooks", lifespan=lifespan)


# -------------------------
# Health & root
# -------------------------
@app.get("/health")
async def health():
    return PlainTextResponse("ok")


@app.get("/")
async def root():
    return PlainTextResponse("ShopBot webhook service")


# -------------------------
# Telegram webhook
# -------------------------
def verify_telegram_secret(request: Request):
    """
    Проверяем заголовок X-Telegram-Bot-Api-Secret-Token и секретный сегмент пути.
    """
    header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if header != WEBHOOK_SECRET:
        # Меньше информации злоумышленнику
        raise HTTPException(status_code=403, detail="forbidden")
    return True


@app.post(TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(request: Request, _ok=Depends(verify_telegram_secret)):
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        log.exception("telegram_webhook error: %s", e)
        # Возвращаем ok, чтобы Телега не долбила ретраями
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": True})


# -------------------------
# Stripe webhook
# -------------------------
@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature")
    if not sig:
        raise HTTPException(status_code=400, detail="missing signature")

    gw = StripeGateway()
    try:
        event = gw.parse_webhook(payload, sig)  # внутри он валидирует подпись
    except Exception as e:
        log.warning("Stripe signature/parse error: %s", e)
        # 400, чтобы Stripe ретраил
        raise HTTPException(status_code=400, detail="bad signature")

    etype = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}
    event_id = event.get("id") or "unknown"

    # достаём наш order_uid
    md = obj.get("metadata") or {}
    order_uid = md.get("order_id") or obj.get("client_reference_id")
    if not order_uid:
        log.info("Stripe webhook ignored (no order_id): type=%s id=%s", etype, event_id)
        return JSONResponse({"ok": True})

    order = await Order.get_or_none(order_uid=order_uid)
    if not order:
        log.info("Unknown order_uid=%s (event=%s)", order_uid, event_id)
        return JSONResponse({"ok": True})

    try:
        if etype == "checkout.session.completed":
            order.provider = "stripe"
            order.stripe_session_id = obj.get("id") or order.stripe_session_id
            pi = obj.get("payment_intent")
            if isinstance(pi, str):
                order.stripe_payment_intent = pi
            amount_total = obj.get("amount_total")  # всегда в центах
            currency = obj.get("currency")
            if amount_total is not None:
                order.amount_cents = int(amount_total)
            if currency:
                order.currency = currency.upper()

            order.status = "paid"
            await order.save()
            try:
                mid = await storage.redis.get(f"paymsg:{order.order_uid}")
                if mid:
                    await bot.delete_message(chat_id=order.user.id, message_id=int(mid))
                    await storage.redis.delete(f"paymsg:{order.order_uid}")
            except Exception:
                pass

            if not order.notified_paid:
                order.notified_paid = True
                await order.save()
                asyncio.create_task(_notify_user_success(order.id))

        elif etype == "payment_intent.succeeded":
            order.provider = "stripe"
            order.stripe_payment_intent = obj.get("id") or order.stripe_payment_intent
            order.status = "paid"
            await order.save()

            if not order.notified_paid:
                order.notified_paid = True
                await order.save()
                asyncio.create_task(_notify_user_success(order.id))

        elif etype == "payment_intent.payment_failed":
            if order.status != "paid":
                order.status = "failed"
                await order.save()

        elif etype == "checkout.session.expired":
            # если уже cancelled через /cancel — не перетираем
            if order.status not in ("paid", "cancelled"):
                order.status = "expired"
                await order.save()

        else:
            # остальные типы тебе не нужны
            pass

    except Exception as e:
        log.exception("Stripe webhook update error: %s", e)
        # 500, чтобы был ретрай
        raise HTTPException(status_code=500, detail="update error")

    return JSONResponse({"ok": True})


@app.get("/pay/success")
async def success(order_id: str = "", sig: str = ""):
    if not _verify(order_id, sig):
        return PlainTextResponse("bad signature", status_code=400)
        # никаких уведомлений и флагов — истина придёт через вебхук
    return _tg_redirect_html(BOT_USERNAME, order_id)


@app.get("/pay/cancel")
async def cancel(order_id: str = "", sig: str = ""):
    if not _verify(order_id, sig):
        return PlainTextResponse("bad signature", status_code=400)

    order = await Order.get_or_none(order_uid=order_id)
    if not order:
        # редиректим в бота, чтобы не зависать на пустой странице
        return _tg_redirect_html(BOT_USERNAME, order_id)

    try:
        mid = await storage.redis.get(f"paymsg:{order.order_uid}")
        if mid:
            await bot.delete_message(chat_id=order.user.id, message_id=int(mid))
            await storage.redis.delete(f"paymsg:{order.order_uid}")
    except Exception:
        pass
        # не спорим с успешной оплатой
    if order.status != "paid":
        order.status = "cancelled"

    # шлём уведомление ровно один раз
    if not order.notified_cancel:
        order.notified_cancel = True
        await order.save()
        asyncio.create_task(_notify_user_cancel(order.id))
    else:
        await order.save()

    return _tg_redirect_html(BOT_USERNAME, order_id)


# -------------------------
# Cryptomus webhook
# -------------------------
async def webhook_cryptomus(request: Request):
    raw = await request.body()
    signature = request.headers.get("sign") or request.headers.get("Sign") or ""
    gw = CryptomusGateway()

    # 1) Подпись
    try:
        body = gw.verify_webhook(raw, signature)  # dict БЕЗ поля sign
    except Exception:
        log.warning("Cryptomus signature error")
        # 400 — пусть ретраят
        raise HTTPException(status_code=400, detail="bad signature")

    # 2) Базовые поля
    order_uid = str(body.get("order_id") or "").strip()
    status = str(body.get("status") or "").lower()
    uuid = body.get("uuid") or body.get("payment_id")  # invoice uuid

    pay_amt = body.get("amount")  # сумма в мерчант-валюте (строка)
    pay_cur = (body.get("currency") or "").upper()
    payer_amt = body.get("payment_amount")  # сумма в криптовалюте (строка/число)
    payer_cur = (body.get("payer_currency") or "").upper()
    network = (body.get("network") or "").lower()

    if not order_uid:
        log.info("Cryptomus webhook ignored: no order_id, status=%s", status)
        return JSONResponse({"ok": True})

    # 3) Ищем заказ
    order = await Order.get_or_none(order_uid=order_uid)
    if not order:
        log.warning("Cryptomus webhook for unknown order_uid=%s", order_uid)
        return JSONResponse({"ok": True})

    # 4) Сверки суммы/валюты (мягко)
    try:
        if pay_amt is not None and getattr(order, "amount_cents", None) not in (
            None,
            0,
        ):
            cents = int(
                (Decimal(str(pay_amt)) * 100).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
            if int(order.amount_cents) != cents:
                log.warning(
                    "Cryptomus amount mismatch for %s: expected=%s got=%s cents",
                    order.order_uid,
                    order.amount_cents,
                    cents,
                )
                return JSONResponse({"ok": True})
        if pay_cur and getattr(order, "currency", None):
            if order.currency.upper() != pay_cur.upper():
                log.warning(
                    "Cryptomus currency mismatch for %s: expected=%s got=%s",
                    order.order_uid,
                    order.currency,
                    pay_cur,
                )
                return JSONResponse({"ok": True})
    except Exception as e:
        # не валим вебхук, просто отметим
        log.exception("Cryptomus amount/currency check error: %s", e)
        return JSONResponse({"ok": True})

    # 5) Сохраним provider/txid и meta независимо от статуса
    try:
        order.provider = "cryptomus"
        if uuid and (order.txid or "") != str(uuid):
            order.txid = str(uuid)

        meta = dict(order.meta or {})
        meta["cryptomus"] = {
            "uuid": uuid,
            "payer_amount": payer_amt,
            "payer_currency": payer_cur,
            "merchant_amount": pay_amt,
            "merchant_currency": pay_cur,
            "network": network,
            "last_status": status,
        }
        order.meta = meta
    except Exception:
        # мета не критична
        pass

    # 6) Маппинг статусов → апдейты и нотификации в фоне
    try:
        if status in ("paid", "paid_over"):
            # Идемпотентность
            if order.status != "paid":
                # Зафиксируем сумму/валюту, если пришли
                try:
                    if pay_amt is not None:
                        order.amount_cents = int(
                            (Decimal(str(pay_amt)) * 100).quantize(
                                Decimal("1"), rounding=ROUND_HALF_UP
                            )
                        )
                except Exception:
                    pass
                if pay_cur:
                    order.currency = pay_cur.upper()

                order.status = "paid"
                await order.save()

            if not order.notified_paid:
                order.notified_paid = True
                await order.save()
                asyncio.create_task(_notify_user_success(order.id))

            return JSONResponse({"ok": True})

        if status in ("cancel", "canceled", "cancelled"):
            # Не перетираем успешный платёж
            if order.status not in ("paid", "cancelled"):
                order.status = "cancelled"
                await order.save()

            if not order.notified_cancel:
                order.notified_cancel = True
                await order.save()
                asyncio.create_task(_notify_user_cancel(order.id))

            return JSONResponse({"ok": True})

        if status in ("fail", "system_fail"):
            if order.status != "paid":
                order.status = "failed"
                await order.save()
            return JSONResponse({"ok": True})

        # confirm_check / check / wrong_amount / expired / и т.д. — просто логируем
        log.info("Cryptomus webhook ignored: status=%s order=%s", status, order_uid)
        return JSONResponse({"ok": True})

    except Exception as e:
        log.exception("Cryptomus webhook update error: %s", e)
        # 500 → ретрай
        raise HTTPException(status_code=500, detail="update error")
