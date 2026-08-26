"""Бизнес-логика заказа: собрать, сохранить, отметить оплату, известить.

Про http здесь ничего не знают — этот слой одинаково работает и для
карточной оплаты, и для оплаты при встрече, и для тестового шлюза.
"""

import datetime as dt
import logging
import random
from typing import Any

from psycopg.types.json import Jsonb

from . import catalog, notify
from .db import pool

log = logging.getLogger("shop.orders")

MAX_LINES = 20          # больше позиций в одном заказе не бывает
MAX_QTY = 10            # штук одного товара


class OrderError(ValueError):
    """Заказ не принят: с ним что-то не так со стороны покупателя."""


def build_items(raw: list[dict[str, Any]], locale: str) -> list[dict[str, Any]]:
    """Превращает то, что прислала витрина, в позиции с ценами сервера."""
    if not raw:
        raise OrderError("пустая корзина")
    if len(raw) > MAX_LINES:
        raise OrderError("слишком много позиций")

    items = []
    for line in raw:
        qty = line.get("qty")
        if not isinstance(qty, int) or not 1 <= qty <= MAX_QTY:
            raise OrderError("непонятное количество")
        try:
            item = catalog.resolve(str(line.get("sku", "")), locale)
        except catalog.CatalogError as e:
            raise OrderError(str(e)) from e
        item["qty"] = qty
        items.append(item)
    return items


def create(method: str, locale: str, items: list[dict[str, Any]], customer: dict[str, str]) -> dict[str, Any]:
    status = "cash_pending" if method == "cash_pickup" else "awaiting_payment"
    amount = sum(i["unit_cents"] * i["qty"] for i in items)

    with pool.connection() as conn:
        for _ in range(5):                      # номер случайный, изредка бывает занят
            number = _new_number()
            row = conn.execute(
                """INSERT INTO orders (number, status, method, locale, amount_cents, items, customer)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (number) DO NOTHING
                   RETURNING *""",
                (number, status, method, locale, amount, Jsonb(items), Jsonb(customer)),
            ).fetchone()
            if row:
                log.info("заказ %s создан: %s, %s центов", number, method, amount)
                return row
    raise RuntimeError("не удалось выдать номер заказа")


def get(number: str) -> dict[str, Any] | None:
    with pool.connection() as conn:
        return conn.execute("SELECT * FROM orders WHERE number = %s", (number,)).fetchone()


def mark_paid(number: str, customer: dict[str, str], session_id: str | None = None) -> dict[str, Any] | None:
    """Отмечает оплату. Возвращает заказ, если это первая оплата, иначе None.

    Через эту дверь проходят и вебхук stripe, и тестовый шлюз, поэтому
    повторный вызов по тому же заказу безопасен: второго алерта не будет.
    """
    with pool.connection() as conn:
        row = conn.execute(
            """UPDATE orders
                  SET status = 'paid',
                      paid_at = now(),
                      stripe_session_id = COALESCE(%s, stripe_session_id),
                      customer = customer || %s
                WHERE number = %s AND status <> 'paid'
            RETURNING *""",
            (session_id, Jsonb(customer), number),
        ).fetchone()
    if row is None:
        log.info("заказ %s уже был оплачен — повтор пропущен", number)
        return None
    log.info("заказ %s оплачен", number)
    return row


def attach_customer(number: str, customer: dict[str, str], session_id: str | None) -> dict[str, Any] | None:
    """Дописывает контакты к ещё не оплаченному заказу, не трогая статус.

    Так приходят отложенные способы оплаты вроде multibanco: человек уже
    оставил свои данные и получил реквизиты, а деньги придут через день-два.
    """
    with pool.connection() as conn:
        row = conn.execute(
            """UPDATE orders
                  SET stripe_session_id = COALESCE(%s, stripe_session_id),
                      customer = customer || %s
                WHERE number = %s AND status = 'awaiting_payment'
            RETURNING *""",
            (session_id, Jsonb(customer), number),
        ).fetchone()
    if row is not None:
        log.info("заказ %s ждёт отложенной оплаты", number)
    return row


def mark_cancelled(number: str) -> dict[str, Any] | None:
    """Оплата не состоялась. Возвращает заказ, если это первая отмена."""
    with pool.connection() as conn:
        row = conn.execute(
            """UPDATE orders SET status = 'cancelled'
                WHERE number = %s AND status = 'awaiting_payment'
            RETURNING *""",
            (number,),
        ).fetchone()
    if row is not None:
        log.info("заказ %s отменён: оплата не прошла", number)
    return row


def announce(order: dict[str, Any]) -> None:
    """Шлёт алерт админу и запоминает, что он ушёл."""
    if notify.send(notify.order_message(order)):
        with pool.connection() as conn:
            conn.execute("UPDATE orders SET notified_at = now() WHERE id = %s", (order["id"],))
    else:
        log.error("алерт по заказу %s не ушёл, попробуем ещё раз", order["number"])


def resend_missed(older_than_seconds: int = 60) -> int:
    """Повторяет алерты, которые не дошли: телеграм мог быть недоступен."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=older_than_seconds)
    with pool.connection() as conn:
        rows = conn.execute(
            """SELECT * FROM orders
                WHERE notified_at IS NULL AND created_at < %s
                  AND status IN ('paid', 'cash_pending')
                ORDER BY created_at LIMIT 20""",
            (cutoff,),
        ).fetchall()
    for row in rows:
        announce(row)
    return len(rows)


def _new_number() -> str:
    day = dt.datetime.now(dt.timezone.utc).strftime("%y%m%d")
    return f"SP-{day}-{random.randint(1000, 9999)}"
