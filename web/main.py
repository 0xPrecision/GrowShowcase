import asyncio
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse

from aiogram import Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.redis import RedisStorage


from database.init_db import init_db, close_db
from database.models import Order, OrderItem
from keyboards.user_kb.order_keyboards import order_details_keyboard
from web.main_helper import _tg_redirect_html
from config_data.bot_instance import bot

from payments.cryptomus_gateway import CryptomusGateway
from payments.stripe_gateway import StripeGateway

from services.i18n.middleware import LocaleMiddleware
from services.i18n.translations import Translator
from services.i18n.bridge import tr, pick_locale, use_locale
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
    # 1) Подпись и парсинг
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature")
    if not sig:
        raise HTTPException(status_code=400, detail="missing signature")

    gw = StripeGateway()
    try:
        event = gw.parse_webhook(payload, sig)
    except Exception as e:
        log.warning("Stripe signature/parse error: %s", e)
        # 400 — пусть Stripe ретраит
        raise HTTPException(status_code=400, detail="bad signature")

    etype = event.get("type")
    obj = (event.get("data") or {}).get("object") or {}
    event_id = event.get("id") or "unknown"

    # 2) Оставляем только финальные события
    # основной путь — checkout.session.completed с payment_status=paid
    # резерв — payment_intent.succeeded
    data = StripeGateway.extract_success(event)
    if not data or not data.get("order_id"):
        log.info("Stripe webhook ignored: type=%s id=%s", etype, event_id)
        return JSONResponse({"ok": True})

    is_canceled = etype in ("checkout.session.expired", "payment_intent.canceled")
    is_failed = etype in ("payment_intent.payment_failed",)

    if data and data.get("order_id") and not (is_canceled or is_failed):
        order_uid = data["order_id"]
        try:
            order = await Order.get_or_none(order_uid=order_uid)
            if not order:
                log.warning(
                    "Stripe webhook for unknown order_uid=%s (event=%s)",
                    order_uid,
                    event_id,
                )
                return JSONResponse({"ok": True})
        except Exception as e:
            log.exception("Stripe order fetch error: %s", e)
            # 500 — чтобы был ретрай
            raise HTTPException(status_code=500, detail="db error")

        # 4) Дедупликация: если уже оплачен — выходим тихо
        if order.status == "paid":
            log.info(
                "Stripe webhook duplicate for paid order_uid=%s (event=%s)",
                order.order_uid,
                event_id,
            )
            return JSONResponse({"ok": True})

        # 5) Сверка суммы/валюты
        try:
            amt = data.get("amount_cents")
            cur = data.get("currency")
            if amt is not None and getattr(order, "amount_cents", None) not in (
                None,
                0,
            ):
                if int(order.amount_cents) != int(amt):
                    log.warning(
                        "Amount mismatch for order_uid=%s: expected=%s got=%s (event=%s)",
                        order.order_uid,
                        order.amount_cents,
                        amt,
                        event_id,
                    )
                    return JSONResponse({"ok": True})
            if cur and getattr(order, "currency", None):
                if order.currency.upper() != cur.upper():
                    log.warning(
                        "Currency mismatch for order_uid=%s: expected=%s got=%s (event=%s)",
                        order.order_uid,
                        order.currency,
                        cur,
                        event_id,
                    )
                    return JSONResponse({"ok": True})
        except Exception as e:
            log.exception("Stripe amount/currency check error: %s", e)
            raise HTTPException(status_code=500, detail="validation error")

        # 6) Доп. сверка позиций корзины (если передаёшь items_count в metadata)
        try:
            md = obj.get("metadata") or {}
            items_count_md = md.get("items_count")
            if items_count_md is not None:
                try:
                    expected = int(items_count_md)
                    # считаем фактические позиции — можно оптимизировать, если ты уже префетчишь
                    actual = await OrderItem.filter(order=order).count()
                    if actual != expected:
                        log.warning(
                            "Items count mismatch for order_uid=%s: expected=%s got=%s (event=%s)",
                            order.order_uid,
                            expected,
                            actual,
                            event_id,
                        )
                        return JSONResponse({"ok": True})
                except Exception:
                    # если парс счёта не удался — не валим, просто логируем
                    log.warning(
                        "Invalid items_count in metadata for order_uid=%s (event=%s)",
                        order.order_uid,
                        event_id,
                    )
        except Exception as e:
            log.exception("Stripe items_count check error: %s", e)
            raise HTTPException(status_code=500, detail="validation error")

        # 7) Сохраняем Stripe айдишники и подтверждаем оплату
        try:
            if etype == "checkout.session.completed":
                order.stripe_session_id = obj.get("id") or order.stripe_session_id
                pi = obj.get("payment_intent")
                if isinstance(pi, str):
                    order.stripe_payment_intent = pi
            elif etype == "payment_intent.succeeded":
                order.stripe_payment_intent = (
                    obj.get("id") or order.stripe_payment_intent
                )

            order.provider = "stripe"
            if data.get("amount_cents") is not None:
                order.amount_cents = int(data["amount_cents"])
            if data.get("currency"):
                order.currency = data["currency"].upper()

            order.status = "paid"
            await order.save()
        except Exception as e:
            log.exception("Stripe order update error: %s", e)
            # 500 — пусть прилетит повтор
            raise HTTPException(status_code=500, detail="update error")

        try:
            await order.fetch_related("user", "user__locale_pref")

            user_locale = getattr(
                getattr(order.user, "locale_pref", None), "locale", None
            )
            loc = pick_locale(user_locale, "en")
            amount_str = f"{order.total_price} {order.currency}"

            with use_locale(loc):
                text_user = tr(
                    "user_checkout.messages.spasibo-vash-zakaz-oformlen",
                    order_id=order.order_uid,
                    amount=amount_str,
                )
                btn_text_order = tr("order_keyboards.buttons.k-spisku-zakazov")
                btn_text_menu = tr("order_keyboards.buttons.v-glavnoe-menyu")

                text_admin = tr(
                    "user_checkout_utils.misc.soobschenie-dlya-administratora",
                    id=order.order_uid,
                    full_name=order.client_name,
                    total=order.total_price,
                    currency="$",
                    comment=order.comment,
                )

            user_take = await Order.filter(id=order.id, notified_user=False).update(
                notified_user=True
            )
            if user_take == 1:
                try:
                    msg = await bot.send_message(
                        chat_id=order.user.id,
                        text=text_user,
                        reply_markup=order_details_keyboard(
                            text_order=btn_text_order, text_menu=btn_text_menu
                        ),
                    )
                    await asyncio.sleep(120)
                    await bot.delete_message(
                        chat_id=order.user.id, message_id=msg.message_id
                    )

                except Exception as e:
                    log.exception(
                        "User notify failed for order_uid=%s: %s", order.order_uid, e
                    )
                    await Order.filter(id=order.id).update(notified_user=False)

            admin_id = int(os.getenv("GROUP_ID"))
            await bot.send_message(chat_id=admin_id, text=text_admin)

        except Exception as e:
            log.exception("Notify failed for order_uid=%s: %s", order.order_uid, e)

        return JSONResponse({"ok": True})

    # === Отмена / Просрочка / Фейл ===

    # Вытаскиваем order_id из metadata хотя бы
    md = obj.get("metadata") or {}
    order_uid = md.get("order_id")
    if not order_uid:
        log.info("Stripe webhook ignored (no order_id): type=%s id=%s", etype, event_id)
        return JSONResponse({"ok": True})

    order = await Order.get_or_none(order_uid=order_uid)
    if not order:
        log.info(
            "Stripe webhook for unknown order_uid=%s (event=%s)", order_uid, event_id
        )
        return JSONResponse({"ok": True})

    # Отмена: ставим canceled, если заказ ещё не paid, и шлём сообщение один раз
    if is_canceled:
        try:
            # атомарно переводим в canceled, только если не paid/canceled
            updated = (
                await Order.filter(id=order.id)
                .exclude(status__in=["paid", "canceled"])
                .update(status="canceled")
            )
            if updated == 1:
                await order.fetch_related("user", "user__locale_pref")
                user_locale = getattr(
                    getattr(order.user, "locale_pref", None), "locale", None
                )
                loc = pick_locale(user_locale, "en")
                with use_locale(loc):
                    text_user = tr(
                        "user_checkout.messages.oplata_otmenena",
                        order_id=order.order_uid,
                    )
                try:
                    msg = await bot.send_message(chat_id=order.user.id, text=text_user)
                    await asyncio.sleep(120)
                    await bot.delete_message(
                        chat_id=order.user.id, message_id=msg.message_id
                    )
                except Exception as e:
                    log.exception(
                        "Cancel notify failed for order_uid=%s: %s", order.order_uid, e
                    )

                admin_id = int(os.getenv("GROUP_ID", "0")) or None
                if admin_id:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"⚠️ CANCELED [{order.order_uid}] user {order.client_name}",
                    )
        except Exception as e:
            log.exception(
                "Cancel handling error for order_uid=%s: %s", order.order_uid, e
            )
            raise HTTPException(status_code=500, detail="cancel update error")

        return JSONResponse({"ok": True})

    # Фейл платежа: помечаем failed, без пинания пользователя “отменой”
    if is_failed:
        try:
            await Order.filter(id=order.id).exclude(status__in=["paid"]).update(
                status="failed"
            )
            admin_id = int(os.getenv("GROUP_ID", "0")) or None
            if admin_id:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"❌ FAILED [{order.order_uid}] user {order.user.id}",
                )
        except Exception as e:
            log.exception(
                "Fail handling error for order_uid=%s: %s", order.order_uid, e
            )
            raise HTTPException(status_code=500, detail="fail update error")

        return JSONResponse({"ok": True})

    # Всё остальное игнорируем тихо
    log.info("Stripe webhook ignored: type=%s id=%s", etype, event_id)
    return JSONResponse({"ok": True})


@app.get("/success")
async def success(order_id: str = ""):
    return _tg_redirect_html(BOT_USERNAME, order_id)


@app.get("/cancel")
async def cancel(order_id: str = ""):
    return _tg_redirect_html(BOT_USERNAME, order_id)

@app.get("/pay/success")
async def pay_success_alias(order_id: str = ""):
    return await success(order_id)  # reuse

@app.get("/pay/cancel")
async def pay_cancel_alias(order_id: str = ""):
    return await cancel(order_id)   # reuse


# -------------------------
# Cryptomus webhook
# -------------------------
@app.post("/webhook/cryptomus")
async def webhook_cryptomus(request: Request):
    raw = await request.body()
    signature = request.headers.get("sign") or request.headers.get("Sign") or ""
    gw = CryptomusGateway()

    # 1) подпись
    try:
        body = gw.verify_webhook(raw, signature)  # должен вернуть dict БЕЗ поля sign
    except Exception:
        log.warning("Cryptomus signature error")
        # 400 — чтобы сервис ретраил, а мы не потеряли событие
        raise HTTPException(status_code=400, detail="bad signature")

    # 2) вытащим базовое
    # ожидаемые ключи: order_id, status, amount, currency, payment_amount, payer_currency, network, uuid etc.
    order_uid = str(body.get("order_id") or "").strip()
    status = str(body.get("status") or "").lower()
    uuid = body.get("uuid") or body.get("payment_id")  # invoice uuid
    pay_amt = body.get("amount")  # сумма в твоей валюте (например, USD строкой)
    pay_cur = (body.get("currency") or "").upper()
    payer_amt = body.get("payment_amount")  # в криптовалюте
    payer_cur = (body.get("payer_currency") or "").upper()
    network = (body.get("network") or "").lower()

    if not order_uid:
        log.info("Cryptomus webhook ignored: no order_id, status=%s", status)
        return JSONResponse({"ok": True})

    # 3) найдём заказ
    order = await Order.get_or_none(order_uid=order_uid)
    if not order:
        log.warning("Cryptomus webhook for unknown order_uid=%s", order_uid)
        return JSONResponse({"ok": True})

    # 4) вытащим деньги/сверки
    try:
        # сверка суммы в merchant валюте (если в заказе есть amount_cents)
        if pay_amt is not None and getattr(order, "amount_cents", None) not in (
            None,
            0,
        ):
            # pay_amt обычно строка типа "2.00" → переводим в центы аккуратно
            from decimal import Decimal, ROUND_HALF_UP

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
                # не валим, просто игнорим событие
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
        log.exception("Cryptomus amount/currency check error: %s", e)
        raise HTTPException(status_code=500, detail="validation error")

    # 5) сохраним метаданные
    try:
        # обновим txid и meta независимо от статуса
        if uuid and (order.txid or "") != str(uuid):
            order.txid = str(uuid)
        # наполняем meta
        meta = dict(order.meta or {})
        meta.update(
            {
                "cryptomus": {
                    "uuid": uuid,
                    "payer_amount": payer_amt,
                    "payer_currency": payer_cur,
                    "merchant_amount": pay_amt,
                    "merchant_currency": pay_cur,
                    "network": network,
                    "last_status": status,
                }
            }
        )
        order.meta = meta
    except Exception:
        pass  # мета не критична
    # 6) маппинг статусов
    if status in ("paid", "paid_over"):
        # если уже paid — тихо выходим
        if order.status == "paid":
            return JSONResponse({"ok": True})

        order.provider = "cryptomus"
        # если в вебхуке пришла сумма — зафиксируем
        try:
            if pay_amt is not None:
                from decimal import Decimal, ROUND_HALF_UP

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

        # идемпотентная нотификация пользователя (если хочешь оповещать из вебхука)
        try:
            take = await Order.filter(id=order.id, notified_user=False).update(
                notified_user=True
            )
            await order.fetch_related("user", "user__locale_pref")
            loc = pick_locale(
                getattr(getattr(order.user, "locale_pref", None), "locale", None), "en"
            )
            amount_str = f"{order.total_price} {order.currency}"
            if take == 1:
                with use_locale(loc):
                    text_user = tr(
                        "user_checkout.messages.spasibo-vash-zakaz-oformlen",
                        order_id=order.order_uid,
                        amount=amount_str,
                    )
                try:
                    msg = await bot.send_message(chat_id=order.user.id, text=text_user)
                    await asyncio.sleep(60)
                    await bot.delete_message(
                        chat_id=order.user.id, message_id=msg.message_id
                    )
                except Exception as e:
                    log.exception("Cryptomus user notify failed: %s", e)
                    await Order.filter(id=order.id).update(notified_user=False)
        except Exception as e:
            log.exception("Cryptomus notify wrap failed: %s", e)

        try:
            admin_id = int(os.getenv("GROUP_ID", "0")) or None
            if admin_id:
                await bot.send_message(
                    admin_id,
                    f"💸 PAID [CM] [{order.order_uid}] {order.total_price} {order.currency} | user {order.client_name}",
                )
        except Exception:
            pass

        return JSONResponse({"ok": True})

    if status == "cancel":
        # атомарно переведём в canceled, если ещё не paid/canceled
        updated = (
            await Order.filter(id=order.id)
            .exclude(status__in=["paid", "canceled"])
            .update(status="canceled")
        )
        if updated == 1:
            await order.fetch_related("user", "user__locale_pref")
            loc = pick_locale(
                getattr(getattr(order.user, "locale_pref", None), "locale", None), "en"
            )
            with use_locale(loc):
                text_user = tr(
                    "user_checkout.messages.oplata_otmenena", order_id=order.order_uid
                )
            try:
                msg = await bot.send_message(chat_id=order.user.id, text=text_user)
                await asyncio.sleep(60)
                await bot.delete_message(
                    chat_id=order.user.id, message_id=msg.message_id
                )
            except Exception as e:
                log.exception("Cryptomus cancel notify failed: %s", e)
            try:
                admin_id = int(os.getenv("GROUP_ID", "0")) or None
                if admin_id:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ CANCELED [CM] [{order.order_uid}] user {order.user.id}",
                    )
            except Exception:
                pass
        return JSONResponse({"ok": True})

    if status in ("fail", "system_fail"):
        await Order.filter(id=order.id).exclude(status__in=["paid"]).update(
            status="failed"
        )
        try:
            admin_id = int(os.getenv("GROUP_ID", "0")) or None
            if admin_id:
                await bot.send_message(
                    admin_id,
                    f"❌ FAILED [CM] [{order.order_uid}] user {order.client_name}",
                )
        except Exception:
            pass
        return JSONResponse({"ok": True})

    # всё прочее игнорим: confirm_check / check / wrong_amount и т.п.
    log.info("Cryptomus webhook ignored: status=%s order=%s", status, order_uid)
    return JSONResponse({"ok": True})
