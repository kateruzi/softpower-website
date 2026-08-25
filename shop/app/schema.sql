-- Заказы магазина. Схема создаётся при старте сервиса и меняется только
-- добавлением новых полей — старые не переименовываем и не удаляем,
-- иначе выкатка новой версии уронит приём заказов.

CREATE TABLE IF NOT EXISTS orders (
    id                BIGSERIAL PRIMARY KEY,
    number            TEXT UNIQUE NOT NULL,        -- SP-260825-4213, его видит покупатель
    status            TEXT NOT NULL,               -- awaiting_payment | paid | cash_pending | cancelled
    method            TEXT NOT NULL,               -- card | cash_pickup
    locale            TEXT NOT NULL,               -- ru | en
    amount_cents      INTEGER NOT NULL,
    currency          TEXT NOT NULL DEFAULT 'eur',
    items             JSONB NOT NULL,              -- [{sku, qty, title, unit_cents}]
    customer          JSONB NOT NULL DEFAULT '{}', -- имя, контакт, телефон, комментарий
    stripe_session_id TEXT UNIQUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at           TIMESTAMPTZ,
    notified_at       TIMESTAMPTZ                  -- когда алерт реально ушёл в телеграм
);

CREATE INDEX IF NOT EXISTS orders_unnotified
    ON orders (created_at) WHERE notified_at IS NULL;

-- Stripe присылает один и тот же вебхук несколько раз: по id события
-- отличаем повтор от нового и не шлём второй алерт на тот же заказ.
CREATE TABLE IF NOT EXISTS stripe_events (
    id          TEXT PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
