"""HTTP-слой: тонкий. Проверить вход → позвать логику → отдать ответ.

Адреса заданы витриной (js/merch-shop.js) и менять их нельзя без правки
обеих языковых страниц: /api/stock, /api/checkout, /api/order.
"""

import asyncio
import collections
import logging
import pathlib
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import catalog, db, notify, orders, payments
from .config import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("shop.api")

app = FastAPI(title="soft power shop", docs_url=None, redoc_url=None, openapi_url=None)

SITE_CATALOG = pathlib.Path("/site/js/merch-catalog.js")   # витрина, только на чтение


# ── что присылает витрина ───────────────────────────────────────────────
class Line(BaseModel):
    sku: str = Field(max_length=200)
    qty: int = Field(ge=1, le=orders.MAX_QTY)


class Customer(BaseModel):
    name: str = Field(default="", max_length=200)
    contact: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=60)
    comment: str = Field(default="", max_length=2000)


class CheckoutIn(BaseModel):
    items: list[Line] = Field(max_length=orders.MAX_LINES)
    locale: str = Field(default="ru", pattern="^(ru|en)$")
    method: str = Field(default="card", pattern="^card$")


class OrderIn(BaseModel):
    items: list[Line] = Field(max_length=orders.MAX_LINES)
    locale: str = Field(default="ru", pattern="^(ru|en)$")
    method: str = Field(default="cash_pickup", pattern="^cash_pickup$")
    customer: Customer


# ── защита от спама: заказ никого не аутентифицирует, адрес открыт всем.
# Считаем только заказы, которые реально завелись: отклонённый мусор
# лимит не съедает, иначе опечатка покупателя закрыла бы ему магазин на час ──
_seen: dict[str, collections.deque] = collections.defaultdict(collections.deque)


def _rate_limit(request: Request) -> None:
    ip = (request.client.host if request.client else "?")
    now = time.monotonic()
    hits = _seen[ip]
    while hits and now - hits[0] > 3600:
        hits.popleft()
    if len(hits) >= config.orders_per_hour:
        log.warning("слишком много заказов с адреса %s", ip)
        raise HTTPException(status_code=429, detail="too many orders")
    hits.append(now)


def _selling_or_503() -> None:
    """Рубильник продаж закрыт — заказ не принимаем, но и не врём об успехе."""
    if not config.can_sell:
        raise HTTPException(status_code=503, detail="магазин сейчас не принимает заказы")


# ── жизненный цикл ──────────────────────────────────────────────────────
@app.on_event("startup")
async def startup() -> None:
    db.start()
    _check_catalogs()
    asyncio.create_task(_retry_loop())
    log.info("сервис поднят: env=%s, stripe=%s, тестовый шлюз=%s",
             config.env, config.stripe_ready, config.fake_payments)


@app.on_event("shutdown")
async def shutdown() -> None:
    db.stop()


def _check_catalogs() -> None:
    """Витрина и серверный каталог должны знать об одних и тех же товарах."""
    if not SITE_CATALOG.exists():
        log.warning("витрина %s не смонтирована — сверку каталогов пропускаю", SITE_CATALOG)
        return
    problems = catalog.mismatch_with_site(SITE_CATALOG.read_text(encoding="utf-8"))
    for problem in problems:
        log.error("каталог: %s", problem)
    if problems:
        notify.send(f"[{config.env}] ВНИМАНИЕ, каталог разъехался:\n" + "\n".join("• " + p for p in problems))


async def _retry_loop() -> None:
    """Алерт мог не уйти — телеграм бывает недоступен. Пробуем ещё."""
    while True:
        await asyncio.sleep(60)
        try:
            await asyncio.to_thread(orders.resend_missed)
        except Exception:                       # фоновая задача не имеет права умереть
            log.exception("повтор алертов сорвался")


# ── витрина ─────────────────────────────────────────────────────────────
@app.get("/api/health")
def health() -> dict[str, Any]:
    """По этому ответу витрина решает, принимать ли заказы по-настоящему."""
    return {"ok": True, "env": config.env, "selling": config.can_sell, "stripe": config.stripe_ready}


@app.get("/api/stock")
def stock() -> dict[str, int]:
    return catalog.stock()


# ── оплата картой ───────────────────────────────────────────────────────
@app.post("/api/checkout")
def checkout(body: CheckoutIn, request: Request) -> dict[str, str]:
    _selling_or_503()
    try:
        items = orders.build_items([line.model_dump() for line in body.items], body.locale)
    except orders.OrderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _rate_limit(request)

    order = orders.create("card", body.locale, items, {})
    try:
        url = payments.checkout_url(order)
    except Exception:
        log.exception("не удалось открыть оплату по заказу %s", order["number"])
        raise HTTPException(status_code=502, detail="payment gateway unavailable")
    return {"url": url}


# ── оплата при встрече ──────────────────────────────────────────────────
@app.post("/api/order")
def order(body: OrderIn, request: Request) -> dict[str, str]:
    _selling_or_503()
    if not body.customer.name or not body.customer.contact:
        raise HTTPException(status_code=400, detail="нужны имя и контакт")
    try:
        items = orders.build_items([line.model_dump() for line in body.items], body.locale)
    except orders.OrderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _rate_limit(request)

    created = orders.create("cash_pickup", body.locale, items, body.customer.model_dump())
    orders.announce(created)
    return {"order": created["number"]}


# ── stripe сообщает об оплате ───────────────────────────────────────────
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request) -> dict[str, bool]:
    payload = await request.body()
    try:
        event = payments.verify_webhook(payload, request.headers.get("stripe-signature", ""))
    except Exception as e:
        log.error("вебхук не прошёл проверку подписи: %s", type(e).__name__)
        raise HTTPException(status_code=400, detail="bad signature")

    with db.pool.connection() as conn:
        fresh = conn.execute(
            "INSERT INTO stripe_events (id) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id",
            (event["id"],),
        ).fetchone()
    if not fresh:
        return {"ok": True}                     # это повтор того же события

    _handle_checkout_event(event)
    return {"ok": True}


def _handle_checkout_event(event: dict[str, Any]) -> None:
    """Что stripe рассказывает про оплату — и что из этого следует.

    Отказ карты события не рождает вовсе: сессия просто не завершается,
    деньги не списываются, покупатель возвращается на страницу мерча.
    А вот отложенные способы (в португалии stripe любит включать multibanco)
    завершают сессию раньше денег, поэтому «завершена» и «оплачена» — разное.
    """
    kind = event["type"]
    if not kind.startswith("checkout.session."):
        return
    session = event["data"]["object"]
    number = session.get("client_reference_id") or (session.get("metadata") or {}).get("order")
    if not number:
        log.error("вебхук %s без номера заказа", kind)
        return

    if kind in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        customer = payments.customer_from_session(session)
        if session.get("payment_status") == "paid":
            changed = orders.mark_paid(number, customer, session.get("id"))
        else:
            changed = orders.attach_customer(number, customer, session.get("id"))
        if changed:
            orders.announce(changed)

    elif kind == "checkout.session.async_payment_failed":
        failed = orders.mark_cancelled(number)
        if failed:
            orders.announce(failed)

    elif kind == "checkout.session.expired":
        # Человек просто закрыл страницу оплаты. Тревожить этим незачем,
        # но и держать заказ вечно ждущим не надо.
        orders.mark_cancelled(number)


# ── тестовый шлюз оплаты: только staging ────────────────────────────────
def _dev_only() -> None:
    if not config.fake_payments:
        raise HTTPException(status_code=404, detail="not found")


@app.get("/api/dev/pay", response_class=HTMLResponse)
def dev_pay_page(order: str) -> HTMLResponse:
    """Заглушка вместо страницы stripe: тут можно «оплатить» и посмотреть,
    что произойдёт дальше, ровно тем же путём, каким пойдёт настоящая оплата."""
    _dev_only()
    found = orders.get(order)
    if not found:
        raise HTTPException(status_code=404, detail="нет такого заказа")
    total = f"{found['amount_cents'] / 100:.2f} €"
    rows = "".join(f"<li>{i['title']} × {i['qty']}</li>" for i in found["items"])
    return HTMLResponse(f"""<!doctype html><meta charset=utf-8>
<title>тестовая оплата {order}</title>
<style>body{{font:16px/1.5 system-ui;margin:0;display:grid;place-items:center;height:100vh;background:#f4f2ef}}
.box{{background:#fff;padding:32px;border-radius:14px;max-width:420px;box-shadow:0 8px 30px #0001}}
b{{font-size:22px}} ul{{padding-left:18px}} a,button{{font:inherit}}
button{{padding:12px 18px;border:0;border-radius:8px;background:#111;color:#fff;cursor:pointer}}
.cancel{{background:none;color:#888;text-decoration:underline}}
label{{display:block;margin:10px 0;font-size:13px;color:#666}}
label input{{display:block;width:100%;box-sizing:border-box;font:inherit;font-size:14px;
  padding:8px 10px;margin-top:4px;border:1px solid #ddd;border-radius:6px}}</style>
<div class=box>
  <p style="color:#c00">это не stripe, а тестовый шлюз staging</p>
  <p>заказ <b>{order}</b></p>
  <ul>{rows}</ul>
  <p>к оплате <b>{total}</b></p>
  <form method=post action="/api/dev/pay/confirm">
    <input type=hidden name=order value="{order}">
    <label>имя<input name=name value="тестовый покупатель"></label>
    <label>почта<input name=email value="test@example.com"></label>
    <label>телефон<input name=phone value="+351 900 000 000"></label>
    <label>адрес<input name=address value="Rua da Prata 10, 1100-052, Lisboa, PT"></label>
    <label>телеграм<input name=telegram value="@test"></label>
    <button type=submit>оплатить</button>
    <button class=cancel formaction="/api/dev/pay/cancel">отменить</button>
  </form>
</div>""")


@app.post("/api/dev/pay/confirm")
async def dev_pay_confirm(request: Request) -> RedirectResponse:
    _dev_only()
    form = await request.form()
    number = str(form.get("order", ""))
    customer = {
        key: str(form.get(key, "")).strip()
        for key in ("name", "email", "phone", "address", "telegram")
    }
    paid = orders.mark_paid(number, {k: v for k, v in customer.items() if v}, None)
    if paid:
        orders.announce(paid)
    found = paid or orders.get(number)
    if not found:
        raise HTTPException(status_code=404, detail="нет такого заказа")
    return RedirectResponse(payments.success_url(number, found["locale"]) + "&session_id=dev", status_code=303)


@app.post("/api/dev/pay/cancel")
async def dev_pay_cancel(request: Request) -> RedirectResponse:
    _dev_only()
    form = await request.form()
    number = str(form.get("order", ""))
    found = orders.get(number)
    page = "merch-en" if found and found["locale"] == "en" else "merch"
    return RedirectResponse(f"{config.site_url}/{page}", status_code=303)


@app.exception_handler(orders.OrderError)
def order_error(_: Request, exc: orders.OrderError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
