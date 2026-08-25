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

from .config import config

log = logging.getLogger("shop.notify")

_API = "https://api.telegram.org/bot{token}/sendMessage"
_MONEY = "{:.2f} €"


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
    head = {
        "paid": "💶 оплачен картой",
        "cash_pending": "🤝 оплата при встрече",
        "awaiting_payment": "⏳ ждёт оплаты",
    }.get(order["status"], order["status"])

    lines = [
        f"[{config.env}] новый заказ {order['number']}",
        head + " · " + _MONEY.format(order["amount_cents"] / 100),
        "",
    ]
    for item in order["items"]:
        lines.append(f"• {item['title']} × {item['qty']} — " + _MONEY.format(item["unit_cents"] * item["qty"] / 100))

    customer = order.get("customer") or {}
    contacts = [customer.get(k) for k in ("name", "contact", "phone", "email")]
    contacts = [c for c in contacts if c]
    if contacts:
        lines += ["", "покупатель: " + " · ".join(contacts)]
    if customer.get("comment"):
        lines.append("комментарий: " + customer["comment"])

    if order["status"] == "cash_pending":
        lines += ["", "деньги ещё не получены — напиши покупателю про встречу."]
    return "\n".join(lines)
