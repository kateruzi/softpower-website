"""Каталог со стороны сервера: цены, варианты, остатки.

Файл читается при старте и по запросу /api/stock — так правку catalog.json
видно без пересборки образа, достаточно перезапустить контейнер.
"""

import json
import re
from typing import Any

from .config import config


class CatalogError(ValueError):
    """Заказ ссылается на то, чего в каталоге нет."""


def load() -> dict[str, Any]:
    with open(config.catalog_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("products", {})


def parse_sku(sku: str) -> tuple[str, dict[str, str]]:
    """'hoodie|size:lxl' → ('hoodie', {'size': 'lxl'}). Формат задаёт витрина."""
    if not isinstance(sku, str) or not sku or len(sku) > 200:
        raise CatalogError("пустой или слишком длинный sku")
    head, *rest = sku.split("|")
    chosen: dict[str, str] = {}
    for part in rest:
        if part.count(":") != 1:
            raise CatalogError(f"непонятный вариант в sku: {part}")
        key, value = part.split(":")
        chosen[key] = value
    return head, chosen


def _values(spec: Any) -> list[str]:
    """Вариант можно описать списком id или словарём id → подпись."""
    if isinstance(spec, dict):
        return list(spec.get("values", {}))
    return list(spec)


def _option_label(spec: Any, key: str, locale: str) -> str:
    if isinstance(spec, dict):
        return spec.get(locale) or spec.get("ru") or key
    return key


def _value_label(spec: Any, value: str) -> str:
    if isinstance(spec, dict):
        return spec.get("values", {}).get(value) or value
    return value


def resolve(sku: str, locale: str) -> dict[str, Any]:
    """Проверяет sku по каталогу и возвращает название и цену в центах."""
    products = load()
    product_id, chosen = parse_sku(sku)
    product = products.get(product_id)
    if product is None:
        raise CatalogError(f"нет такого товара: {product_id}")

    options = product.get("options", {})
    if set(chosen) != set(options):
        raise CatalogError(f"не те варианты у {product_id}: {sorted(chosen)}")
    for key, value in chosen.items():
        if value not in _values(options[key]):
            raise CatalogError(f"нет варианта {key}={value} у {product_id}")

    if product.get("stock") == 0:
        raise CatalogError(f"{product_id} закончился")

    title = product.get(f"title_{locale}") or product.get("title_ru") or product_id
    if chosen:
        title += " (" + ", ".join(
            f"{_option_label(options[k], k, locale)}: {_value_label(options[k], v)}"
            for k, v in sorted(chosen.items())
        ) + ")"

    return {
        "sku": sku,
        "title": title,
        "unit_cents": int(round(float(product["price_eur"]) * 100)),
    }


def stock() -> dict[str, int]:
    """Остатки по sku для витрины: сейчас на уровне товара, не варианта."""
    out: dict[str, int] = {}
    for product_id, product in load().items():
        qty = product.get("stock")
        if qty is None:
            continue
        options = product.get("options", {})
        for sku in _skus(product_id, options):
            out[sku] = int(qty)
    return out


def _skus(product_id: str, options: dict[str, Any]) -> list[str]:
    skus = [product_id]
    for key in sorted(options):
        skus = [f"{sku}|{key}:{value}" for sku in skus for value in _values(options[key])]
    return skus


def mismatch_with_site(site_catalog_js: str) -> list[str]:
    """Сверяет серверный каталог с витриной и возвращает расхождения.

    Витрина — это js-файл, а не данные, поэтому читаем его грубо: нам нужны
    только id товаров, чтобы заметить «добавили на сайт, забыли на сервере».
    """
    site_ids = set(re.findall(r"^\s*id:\s*'([a-z0-9_-]+)'", site_catalog_js, re.MULTILINE))
    # Первый id внутри блока options — это id варианта, не товара; варианты
    # отсекаем по тому, что у товара следом идёт price.
    product_ids = set(re.findall(r"id:\s*'([a-z0-9_-]+)',[^{}]*?price:", site_catalog_js, re.DOTALL))
    site_ids &= product_ids
    server_ids = set(load())

    problems = []
    for missing in sorted(site_ids - server_ids):
        problems.append(f"товар «{missing}» есть на витрине, но не в shop/catalog.json — купить его нельзя")
    for extra in sorted(server_ids - site_ids):
        problems.append(f"товар «{extra}» есть в shop/catalog.json, но не на витрине")
    return problems
