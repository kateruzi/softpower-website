"""Уведомления в телеграм: бот пишет админу о каждом заказе.

Отправка — обычный вызов Bot API, без sdk. Токен идёт в адресе запроса,
поэтому здесь нигде не печатается ни сам адрес, ни ответ целиком.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from zoneinfo import ZoneInfo

from .config import config

log = logging.getLogger("shop.notify")

_API = "https://api.telegram.org/bot{token}/sendMessage"
_MONEY = "{:.2f} €"
_TZ = ZoneInfo("Europe/Lisbon")

_STATUS = {
    "paid": "💶 оплачен картой",
    "cash_pending": "🤝 оплата при встрече",
    "awaiting_payment": "⏳ ждёт оплаты",
    "cancelled": "❌ оплата не прошла",
}
_TITLE = {"cancelled": "заказ отменён", "awaiting_payment": "заказ ждёт оплаты"}
_METHOD = {"card": "картой онлайн", "cash_pickup": "наличными при встрече"}

# Слева — как поле лежит в customer, справа — как его читать в телеграме.
# Часть полей приходит из формы на сайте, часть со страницы оплаты stripe,
# поэтому в одном заказе набор один, в другом другой — печатаем что есть.
_CUSTOMER_FIELDS = (
    ("name", "имя"),
    ("contact", "связь"),
    ("telegram", "телеграм"),
    ("email", "почта"),
    ("phone", "телефон"),
    ("address", "адрес"),
    ("comment", "комментарий"),
)


def enabled() -> bool:
    return bool(config.telegram_token and config.admin_chat_id)


def send(text: str) -> bool:
    """True — сообщение принято телеграмом. Ошибку не глотаем, а логируем."""
    if not enabled():
        log.warning("телеграм не настроен, сообщение не ушло: %s", text.splitlines()[0])
        return False

    data = urllib.parse.urlencode({
        "chat_id": config.admin_chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()

    request = urllib.request.Request(_API.format(token=config.telegram_token), data=data)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            answer = json.load(response)
        if answer.get("ok"):
            return True
        log.error("телеграм отказал: %s", answer.get("description"))
        return False
    except urllib.error.HTTPError as e:
        log.error("телеграм ответил %s", e.code)
        return False
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        log.error("телеграм недоступен: %s", type(e).__name__)
        return False


def order_message(order: dict[str, Any]) -> str:
    when = (order.get("paid_at") or order["created_at"]).astimezone(_TZ)

    lines = [
        f"[{config.env}] {_TITLE.get(order['status'], 'новый заказ')} {order['number']}",
        _STATUS.get(order["status"], order["status"]) + " · " + _MONEY.format(order["amount_cents"] / 100),
        when.strftime("%d.%m.%Y, %H:%M") + " по лиссабону",
        "",
    ]
    for item in order["items"]:
        lines.append(f"• {item['title']} × {item['qty']} · " + _MONEY.format(item["unit_cents"] * item["qty"] / 100))

    customer = order.get("customer") or {}
    known = [
        (label, str(customer[key]).strip())
        for key, label in _CUSTOMER_FIELDS
        if str(customer.get(key) or "").strip()
    ]
    lines += ["", "покупатель"]
    lines += [f"{label}: {value}" for label, value in known] or ["контактов пока нет, их соберёт страница оплаты"]

    lines += ["", "оплата: " + _METHOD.get(order["method"], order["method"]) + " · страница: " + order["locale"]]

    if order["status"] == "cash_pending":
        lines += ["", "деньги ещё не получены, напиши покупателю про встречу."]
    if order["status"] == "awaiting_payment":
        lines += ["", "способ оплаты отложенный: реквизиты человек получил, деньги придут позже."]
    if order["status"] == "cancelled":
        lines += ["", "деньги не списаны. можно написать и предложить оформить заново."]
    return "\n".join(lines)
