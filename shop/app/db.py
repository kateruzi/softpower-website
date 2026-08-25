"""Доступ к базе: пул соединений и создание схемы при старте."""

import pathlib

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from .config import config

pool = ConnectionPool(config.database_url, min_size=1, max_size=8, open=False, kwargs={"row_factory": dict_row})

_SCHEMA = pathlib.Path(__file__).with_name("schema.sql")


def start() -> None:
    pool.open()
    pool.wait(timeout=30)
    with pool.connection() as conn:
        conn.execute(_SCHEMA.read_text(encoding="utf-8"))


def stop() -> None:
    pool.close()
