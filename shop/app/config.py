"""Единственный слой конфигурации: всё, что берётся из окружения, читается здесь."""

import os


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Config:
    def __init__(self) -> None:
        self.env = os.getenv("SHOP_ENV", "staging")          # staging | prod
        self.database_url = os.environ["DATABASE_URL"]
        self.site_url = os.environ["SITE_URL"].rstrip("/")   # куда возвращать после оплаты
        self.catalog_path = os.getenv("CATALOG_PATH", "/app/catalog.json")

        # Телеграм: бот пишет админу о каждом заказе.
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.admin_chat_id = os.getenv("ADMIN_CHAT_ID", "")

        # Stripe. Пока ключа нет, карточная оплата уходит в тестовый шлюз.
        self.stripe_secret = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

        # Тестовый шлюз оплаты вместо stripe — только для staging.
        self.fake_payments = _bool("DEV_FAKE_PAYMENTS", False)

        # Рубильник продаж: SELLING=0 гасит приём заказов, не трогая сайт.
        # Витрина остаётся, кнопка «оформить заказ» перестаёт отправлять.
        self.selling = _bool("SELLING", True)

        # Защита от спама: сколько заказов с одного адреса пускаем в час.
        self.orders_per_hour = int(os.getenv("ORDERS_PER_HOUR", "10"))

        self._check()

    @property
    def stripe_ready(self) -> bool:
        return bool(self.stripe_secret)

    @property
    def can_sell(self) -> bool:
        """Готов ли сервис реально принять заказ прямо сейчас."""
        return self.selling and (self.stripe_ready or self.fake_payments)

    def _check(self) -> None:
        if self.env == "prod":
            # Боевое окружение не имеет права принимать деньги понарошку.
            if self.fake_payments:
                raise RuntimeError("DEV_FAKE_PAYMENTS=1 в prod — так нельзя")
            if not self.stripe_secret:
                raise RuntimeError("в prod нужен STRIPE_SECRET_KEY")
            if self.stripe_secret.startswith("sk_test_"):
                raise RuntimeError("в prod подставлен тестовый ключ stripe")
        if not self.fake_payments and not self.stripe_secret:
            raise RuntimeError(
                "нечем принимать карты: задай STRIPE_SECRET_KEY "
                "или включи DEV_FAKE_PAYMENTS=1 на staging"
            )


config = Config()
