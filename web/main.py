# web/main.py
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.redis import RedisStorage

from database.init_db import init_db, close_db
from database.models import Order

# Платежные гейтвеи (оставляю как у тебя)
from payments.cryptomus_gateway import CryptomusGateway
from payments.stripe_gateway import StripeGateway

# i18n и локали (как в твоем main.py)
from services.i18n.middleware import LocaleMiddleware
from services.i18n.translations import Translator
from services.locale_repo import LocaleRepo

# -------------------------
# Logging
# -------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("web")

# -------------------------
# ENV
# -------------------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

WEBHOOK_BASE = os.getenv("TELEGRAM_WEBHOOK_URL")  # например: https://bot.example.com
if not WEBHOOK_BASE:
    raise RuntimeError("TELEGRAM_WEBHOOK_URL is not set")

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")  # желательно задать
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Путь вебхука делаем «секретным» через сегмент пути
TELEGRAM_PATH_SEGMENT = WEBHOOK_SECRET if WEBHOOK_SECRET else "telegram"
TELEGRAM_WEBHOOK_PATH = f"/webhook/telegram/{TELEGRAM_PATH_SEGMENT}"
TELEGRAM_WEBHOOK_URL = WEBHOOK_BASE.rstrip("/") + TELEGRAM_WEBHOOK_PATH

# -------------------------
# Bot / Dispatcher
# -------------------------
# parse_mode можно убрать, если тебе не нужен HTML
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)

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
    # Установка вебхука
    try:
        await bot.set_webhook(
            url=TELEGRAM_WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET or None,  # Телега будет слать заголовок X-Telegram-Bot-Api-Secret-Token
            drop_pending_updates=True,
            allowed_updates=["message", "edited_message", "callback_query", "chat_member", "my_chat_member"]
        )
        log.info("Webhook set to %s", TELEGRAM_WEBHOOK_URL)
    except Exception as e:
        log.exception("Failed to set webhook: %s", e)
        raise

    try:
        yield
    finally:
        # Снятие вебхука, закрытие БД и сессии бота
        try:
            await bot.delete_webhook(drop_pending_updates=False)
        except Exception:
            pass
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
    Проверяем заголовок X-Telegram-Bot-Api-Secret-Token, если секрет задан.
    Плюс контролируем сегмент пути ( TELEGRAM_PATH_SEGMENT ).
    """
    if WEBHOOK_SECRET:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header != WEBHOOK_SECRET:
            # Лишние подробности злоумышленникам не нужны
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
    sig = request.headers.get("Stripe-Signature", "")
    gw = StripeGateway()
    try:
        event = gw.parse_webhook(payload, sig)
    except Exception as e:
        log.warning("Stripe signature/parse error: %s", e)
        raise HTTPException(400, str(e))

    data = StripeGateway.extract_success(event)
    if data and data.get("order_id"):
        try:
            order = await Order.get_or_none(order_uid=data["order_id"])
            if order:
                order.status = "paid"
                order.provider = "stripe"
                amount_cents = data.get("amount_cents")
                if amount_cents is not None:
                    setattr(order, "amount_cents", amount_cents)
                currency = data.get("currency")
                if currency:
                    setattr(order, "currency", currency)
                await order.save()
        except Exception as e:
            log.exception("Stripe order update error: %s", e)
            # Не падаем, чтобы не ловить бесконечные ретраи
            return JSONResponse({"ok": True})

    return JSONResponse({"ok": True})

# -------------------------
# Cryptomus webhook
# -------------------------
@app.post("/webhook/cryptomus")
async def webhook_cryptomus(request: Request):
    raw = await request.body()
    signature = request.headers.get("sign") or request.headers.get("Sign") or ""
    gw = CryptomusGateway()
    try:
        body = gw.verify_webhook(raw, signature)
    except Exception as e:
        log.warning("Cryptomus signature error: %s", e)
        raise HTTPException(400, "bad signature")

    data = CryptomusGateway.extract_success(body)
    if data and data.get("order_id"):
        try:
            order = await Order.get_or_none(order_uid=data["order_id"])
            if order:
                order.status = "paid"
                order.provider = "cryptomus"
                txid = data.get("txid")
                if txid:
                    setattr(order, "txid", txid)
                await order.save()
        except Exception as e:
            log.exception("Cryptomus order update error: %s", e)
            return JSONResponse({"ok": True})

    return JSONResponse({"ok": True})



# import os
#
# from aiogram import Bot
# from aiogram.types import Update
# from fastapi import FastAPI, Request, HTTPException
# from fastapi.responses import JSONResponse, PlainTextResponse
# from contextlib import asynccontextmanager
#
# from database.init_db import init_db, close_db
# from database.models import Order
# from payments.cryptomus_gateway import CryptomusGateway
# from payments.stripe_gateway import StripeGateway
#
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await init_db()      # миграции/инициализация соединений
#     try:
#         yield
#     finally:
#         await close_db() # аккуратно закрыть коннекты
#
#
# app = FastAPI(title="ShopBot Webhooks", lifespan=lifespan)
#
#
# @app.get("/health")
# async def health():
#     return PlainTextResponse("ok")
#
# bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
#
# @app.post("/webhook/telegram")
# async def telegram_webhook(request: Request):
#     data = await request.json()
#     update = Update.model_validate(data, context={"bot": bot})
#     # тут твой Dispatcher, не теряй его
#     await dp.feed_update(bot, update)
#     return {"ok": True}
#
# @app.post("/webhook/stripe")
# async def webhook_stripe(request: Request):
#     gw = StripeGateway()
#     payload = await request.body()
#     sig = request.headers.get("Stripe-Signature","")
#     try:
#         event = gw.parse_webhook(payload, sig)
#     except Exception as e:
#         raise HTTPException(400, str(e))
#     data = StripeGateway.extract_success(event)
#     if data and data.get("order_id"):
#         order = await Order.get_or_none(order_uid=data["order_id"])
#         if order:
#             order.status = "paid"
#             order.provider = "stripe"
#             order.amount_cents = data.get("amount_cents") or order.amount_cents
#             order.currency = data.get("currency") or order.currency
#             await order.save()
#     return JSONResponse({"ok": True})
#
# @app.post("/webhook/cryptomus")
# async def webhook_cryptomus(request: Request):
#     gw = CryptomusGateway()
#     raw = await request.body()
#     signature = request.headers.get("sign") or request.headers.get("Sign") or ""
#     try:
#         body = gw.verify_webhook(raw, signature)
#     except Exception as e:
#         raise HTTPException(400, f"bad signature: {e}")
#     data = CryptomusGateway.extract_success(body)
#     if data and data.get("order_id"):
#         order = await Order.get_or_none(order_uid=data["order_id"])
#         if order:
#             order.status = "paid"
#             order.provider = "cryptomus"
#             order.txid = data.get("txid")
#             await order.save()
#     return JSONResponse({"ok": True})
