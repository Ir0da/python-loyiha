import sqlite3
from contextlib import contextmanager

from .config import DB_NAME


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                telegram_id INTEGER,
                role TEXT,
                login TEXT,
                token TEXT,
                PRIMARY KEY (telegram_id, role)
            )
            """
        )


def save_user(telegram_id, role, login, token):
    with _conn() as c:
        c.execute(
            "REPLACE INTO accounts (telegram_id, role, login, token) "
            "VALUES (?, ?, ?, ?)",
            (telegram_id, role, login, token),
        )


def get_token(telegram_id, role):
    with _conn() as c:
        row = c.execute(
            "SELECT token FROM accounts WHERE telegram_id = ? AND role = ?",
            (telegram_id, role),
        ).fetchone()
    return row[0] if row else None


def delete_user(telegram_id, role):
    with _conn() as c:
        c.execute(
            "DELETE FROM accounts WHERE telegram_id = ? AND role = ?",
            (telegram_id, role),
        )