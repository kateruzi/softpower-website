"""Карточная оплата.

Один интерфейс, две реализации: настоящий stripe и тестовый шлюз для
staging. Тестовый существует ровно затем, чтобы можно было пройти
и проверить «что будет после оплаты» до того, как появятся ключи stripe.
Всё, что идёт после оплаты, у обоих одно и то же — общий mark_paid().
"""

import logging
from typing import Any

from .config import config

log = logging.getLogger("shop.payments")

if config.stripe_ready:
    import stripe

    stripe.api_key = config.stripe_secret


def checkout_url(order: dict[str, Any]) -> str:
    """Адрес страницы оплаты, куда витрина отправляет покупателя."""
    if not config.stripe_ready:
        # Тестовый шлюз живёт внутри самого сервиса, см. api.dev_pay_page.
        return f"{config.site_url}/api/dev/pay?order={order['number']}"

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "quantity": item["qty"],
            "price_data": {
                "currency": order["currency"],
                "unit_amount": item["unit_cents"],
                "product_data": {"name": item["title"]},
            },
        } for item in order["items"]],
        locale=order["locale"],
        client_reference_id=order["number"],
        metadata={"order": order["number"]},
        success_url=success_url(order["number"], order["locale"]) + "&session_id={CHECKOUT_SESSION_ID}",
        cancel_url=f"{config.site_url}/{_merch_page(order['locale'])}",
        phone_number_collection={"enabled": True},
        # Вещь шьётся под заказ и едет почтой, поэтому адрес нужен сразу,
        # а телеграм — потому что дальше переписка идёт именно там.
        billing_address_collection="required",
        custom_fields=[{
            "key": "telegram",
            "label": {"type": "custom", "custom": _TELEGRAM_LABEL[order["locale"]]},
            "type": "text",
            "optional": True,
        }],
    )
    return session.url


_TELEGRAM_LABEL = {
    "ru": "телеграм, если удобно",
    "en": "telegram, if that suits you",
}


def success_url(number: str, locale: str) -> str:
    page = "merch-spasibo-en" if locale == "en" else "merch-spasibo"
    return f"{config.site_url}/{page}?order={number}"


def _merch_page(locale: str) -> str:
    return "merch-en" if locale == "en" else "merch"


def customer_from_session(session: Any) -> dict[str, str]:
    """Контакты, которые stripe собрал на своей странице."""
    if not isinstance(session, dict):
        return {}
    details = session.get("customer_details") or {}
    out = {
        "name": details.get("name") or "",
        "email": details.get("email") or "",
        "phone": details.get("phone") or "",
        "address": _one_line(details.get("address")),
        "telegram": _custom_field(session, "telegram"),
    }
    return {k: v for k, v in out.items() if v}


def _one_line(address: Any) -> str:
    """Адрес stripe отдаёт по частям, а читать его в телеграме — одной строкой."""
    if not isinstance(address, dict):
        return ""
    parts = [address.get(k) for k in ("line1", "line2", "postal_code", "city", "state", "country")]
    return ", ".join(p for p in parts if p)


def _custom_field(session: dict[str, Any], key: str) -> str:
    """Значение поля, которое мы сами добавили на страницу оплаты."""
    for field in session.get("custom_fields") or []:
        if isinstance(field, dict) and field.get("key") == key:
            return (field.get("text") or {}).get("value") or ""
    return ""


def verify_webhook(payload: bytes, signature: str) -> Any:
    """Проверяет подпись stripe. Без секрета вебхук не принимаем вовсе."""
    if not config.stripe_webhook_secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET не задан")
    return stripe.Webhook.construct_event(payload, signature, config.stripe_webhook_secret)
