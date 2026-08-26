"""Сводка заказов для дашборда.

Здесь нет ни http, ни базы: на вход идут строки заказов, на выход готовый
к отдаче словарь. Так его легко проверить и легко поменять, не трогая
ни сервис, ни того, кто эту сводку рисует.
"""

import datetime as dt
from collections import Counter
from typing import Any
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Lisbon")

# Заказы, которые считаются состоявшимися: деньги либо пришли, либо придут
# при встрече. Всё остальное в выручку не попадает.
SOLD = ("paid", "cash_pending")

# Порядок статусов в сводке: сначала то, что случилось, потом то, что висит.
STATUSES = ("paid", "cash_pending", "awaiting_payment", "cancelled")


def _eur(cents: Any) -> float:
    return round((cents or 0) / 100, 2)


def _when(value: Any) -> str | None:
    if not isinstance(value, dt.datetime):
        return None
    return value.astimezone(TZ).isoformat(timespec="seconds")


def _order(row: dict[str, Any]) -> dict[str, Any]:
    customer = row.get("customer") or {}
    return {
        "number": row["number"],
        "status": row["status"],
        "method": row["method"],
        "locale": row["locale"],
        "created_at": _when(row.get("created_at")),
        "paid_at": _when(row.get("paid_at")),
        "amount_eur": _eur(row.get("amount_cents")),
        "discount_eur": _eur(row.get("discount_cents")),
        "items": [
            {
                "title": item.get("title", ""),
                "sku": item.get("sku", ""),
                "qty": int(item.get("qty") or 0),
                "unit_eur": _eur(item.get("unit_cents")),
            }
            for item in (row.get("items") or [])
        ],
        # Контакты идут как есть: у карточных заказов свой набор полей,
        # у заказов при встрече свой, и пустые сюда не попадают.
        "customer": {k: v for k, v in customer.items() if v},
    }


def build(rows: list[dict[str, Any]]) -> dict[str, Any]:
    orders = [_order(row) for row in rows]

    by_status: dict[str, dict[str, Any]] = {
        status: {"count": 0, "amount_eur": 0.0} for status in STATUSES
    }
    pieces: Counter[str] = Counter()
    discount = 0.0
    sold_pieces = 0

    for order in orders:
        bucket = by_status.setdefault(order["status"], {"count": 0, "amount_eur": 0.0})
        bucket["count"] += 1
        bucket["amount_eur"] = round(bucket["amount_eur"] + order["amount_eur"], 2)
        discount = round(discount + order["discount_eur"], 2)
        if order["status"] in SOLD:
            for item in order["items"]:
                pieces[item["title"]] += item["qty"]
                sold_pieces += item["qty"]

    earned = round(sum(by_status[s]["amount_eur"] for s in SOLD if s in by_status), 2)

    return {
        "generated_at": dt.datetime.now(TZ).isoformat(timespec="seconds"),
        "currency": "eur",
        "totals": {
            "orders": len(orders),
            "sold_pieces": sold_pieces,
            "earned_eur": earned,
            "paid_eur": by_status["paid"]["amount_eur"],
            "cash_pending_eur": by_status["cash_pending"]["amount_eur"],
            "discount_eur": discount,
            "by_status": by_status,
        },
        # Что именно разобрали: по названию варианта, вместе с размером.
        "pieces": [
            {"title": title, "qty": qty}
            for title, qty in sorted(pieces.items(), key=lambda x: (-x[1], x[0]))
        ],
        "orders": orders,
    }
