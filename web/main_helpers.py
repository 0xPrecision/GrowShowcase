import hashlib
import hmac
import logging
import os

from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from fastapi.responses import HTMLResponse

from config_data.bot_instance import bot
from database.models import Order
from keyboards.user_kb.order_keyboards import order_details_keyboard
from keyboards.user_kb.user_checkout_keyboards import after_cancellation_kb
from services.i18n.bridge import pick_locale, use_locale, tr

load_dotenv()
log = logging.getLogger("web")

PAY_SUCCESS_URL = os.getenv("PAY_SUCCESS_URL")
PAY_CANCEL_URL = os.getenv("PAY_CANCEL_URL")
PAY_FLOW_SECRET = os.getenv("PAY_FLOW_SECRET")

if not PAY_FLOW_SECRET:
    raise RuntimeError("PAY_FLOW_SECRET is required (HMAC for success/cancel).")
if not PAY_SUCCESS_URL or not PAY_CANCEL_URL:
    raise RuntimeError("PAY_SUCCESS_URL and PAY_CANCEL_URL must be set.")


def _tg_redirect_html(bot_username: str, payload: str) -> HTMLResponse:
    tg_deeplink = f"tg://resolve?domain={bot_username}"
    https_fallback = f"https://t.me/{bot_username}"
    html = f"""<!doctype html><html><head>
    <meta charset="utf-8"><title>Redirecting…</title>
    <meta http-equiv="refresh" content="0; url={tg_deeplink}">
    <script>
      window.location = "{tg_deeplink}";
      setTimeout(function(){{ window.location = "{https_fallback}"; }}, 800);
    </script>
    <style>body{{font-family:system-ui,Arial,sans-serif;padding:24px;}}</style>
    </head>
    <body>
      <p>Opening Telegram… If nothing happens, <a href="{https_fallback}">tap here</a>.</p>
    </body></html>"""
    return HTMLResponse(html)


def _sign(uid: str) -> str:
    return hmac.new(PAY_FLOW_SECRET.encode(), uid.encode(), hashlib.sha256).hexdigest()


def _verify(uid: str, sig: str) -> bool:
    if not uid or not sig:
        return False
    want = _sign(uid)
    return hmac.compare_digest(want, sig)


def _append_query(url: str, params: dict) -> str:
    parts = list(urlparse(url))
    query = dict(parse_qsl(parts[4], keep_blank_values=True))
    query.update({k: str(v) for k, v in params.items() if v is not None})
    parts[4] = urlencode(query)
    return urlunparse(parts)


def make_urls(order_uid: str) -> tuple[str, str]:
    sig = _sign(order_uid)
    success_url = _append_query(PAY_SUCCESS_URL, {"order_id": order_uid, "sig": sig})
    cancel_url = _append_query(PAY_CANCEL_URL, {"order_id": order_uid, "sig": sig})
    return success_url, cancel_url


async def _notify_user_success(order_id: int):
    order = await Order.get_or_none(id=order_id)
    if not order:
        return
    await order.fetch_related("user", "user__locale_pref")

    user_locale = getattr(getattr(order.user, "locale_pref", None), "locale", None)
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

    try:
        await bot.send_message(
            chat_id=order.user.id,
            text=text_user,
            reply_markup=order_details_keyboard(
                text_order=btn_text_order, text_menu=btn_text_menu
            ),
        )

    except Exception as e:
        log.exception("User notify failed for order_uid=%s: %s", order.order_uid, e)

    try:
        admin_id = os.getenv("GROUP_ID", "")
        if admin_id:
            await bot.send_message(chat_id=admin_id, text=text_admin)
    except Exception as e:
        log.exception("Notify admin failed for order_uid=%s: %s", order.order_uid, e)


async def _notify_user_cancel(order_id: int):
    order = await Order.get_or_none(id=order_id)
    if not order:
        return

    await order.fetch_related("user", "user__locale_pref")
    loc = pick_locale(
        getattr(getattr(order.user, "locale_pref", None), "locale", None), "en"
    )
    with use_locale(loc):
        text_user = tr(
            "user_checkout.messages.oplata_otmenena")
        text_contact = tr("contact_me")
        text_plans = tr("user_cart_keyboards.buttons.v-katalog")
        text_menu = tr("order_keyboards.buttons.v-glavnoe-menyu")
    try:
        await bot.send_message(chat_id=order.user.id,
                               text=text_user,
                               reply_markup=after_cancellation_kb(text_contact=text_contact,
                                                                  text_plans=text_plans,
                                                                  text_menu=text_menu))
    except Exception as e:
        log.exception("Stripe cancel notify failed: %s", e)
    try:
        admin_id = os.getenv("GROUP_ID", "")
        if admin_id:
            await bot.send_message(
                chat_id=admin_id,
                text=f"⚠️ CANCELED {order.provider} [{order.order_uid}] user {order.user.id}",
            )
    except Exception as e:
        log.exception("Notify admin failed for order_uid=%s: %s", order.order_uid, e)
