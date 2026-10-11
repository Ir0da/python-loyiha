import os
import psycopg2
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")

@contextmanager
def _conn():
    """PostgreSQL bazasiga xavfsiz ulanish yaratish."""
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Bot birinchi marta yonganda accounts jadvalini yaratadi."""
    with _conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                telegram_id BIGINT,
                role TEXT,
                login TEXT,
                token TEXT,
                PRIMARY KEY (telegram_id, role)
            )
            """
        )
        cursor.close()
        print("📊 PostgreSQL ma'lumotlar bazasi va jadvallar muvaffaqiyatli tayyorlandi.")

def save_user(telegram_id, role, login, token):
    """Foydalanuvchi ma'lumotlarini saqlash yoki yangilash (Upsert)."""
    with _conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO accounts (telegram_id, role, login, token)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (telegram_id, role)
            DO UPDATE SET login = EXCLUDED.login, token = EXCLUDED.token
            """,
            (int(telegram_id), str(role), str(login), str(token)),
        )
        cursor.close()

def get_token(telegram_id, role):
    """Foydalanuvchi tokenini bazadan o'qib olish."""
    with _conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT token FROM accounts WHERE telegram_id = %s AND role = %s",
            (int(telegram_id), str(role)),
        )
        row = cursor.fetchone()
        cursor.close()
    return row[0] if row else None

def delete_user(telegram_id, role):
    """Foydalanuvchi tizimdan chiqqanda ma'lumotlarini o'chirish."""
    with _conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM accounts WHERE telegram_id = %s AND role = %s",
            (int(telegram_id), str(role)),
        )
        cursor.close()
