from datetime import date, datetime, timedelta, timezone

from .utils import get_obj_value

try:
    from zoneinfo import ZoneInfo

    UZ_TZ = ZoneInfo("Asia/Tashkent")
except Exception:  # tzdata o'rnatilmagan bo'lsa
    UZ_TZ = timezone(timedelta(hours=5))

WEEKDAYS = [
    "Dushanba", "Seshanba", "Chorshanba", "Payshanba",
    "Juma", "Shanba", "Yakshanba",
]


def now_uz():
    return datetime.now(UZ_TZ)


def today_uz():
    return now_uz().date()


def fmt_date(d):
    return d.strftime("%d.%m.%Y")


def fmt_date_full(d):
    return f"{fmt_date(d)} ({WEEKDAYS[d.weekday()]})"


def parse_user_date(text):
    """'08.10.2026', '08-10-2026', '8/10/2026', '2026-10-08', '08.10' """
    text = (text or "").strip()
    for pattern in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            pass
    try:
        parsed = datetime.strptime(text, "%d.%m")
        return date(today_uz().year, parsed.month, parsed.day)
    except ValueError:
        return None


def item_date(item):
    """Davomat yozuvining sanasi (O'zbekiston vaqti bilan)."""
    value = get_obj_value(item, "lesson_date", "lessonDate", "date")
    if value is None:
        return None

    if isinstance(value, (int, float)) or (
        isinstance(value, str) and value.isdigit()
    ):
        ts = float(value)
        if ts > 1e11:  # millisekund
            ts /= 1000
        return datetime.fromtimestamp(ts, UZ_TZ).date()

    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def lesson_text(item):
    """Masalan: '2-juftlik (09:40-11:00)'"""
    pair = item.get("lessonPair") or item.get("lesson_pair")
    if not isinstance(pair, dict):
        return ""

    name = get_obj_value(pair, "name", default="")
    start = get_obj_value(pair, "start_time", "startTime", default="")
    end = get_obj_value(pair, "end_time", "endTime", default="")

    text = str(name)
    if start and end:
        text += f" ({start}-{end})"
    return text.strip()


def clip_message(text, limit=3900):
    """Telegram 4096 belgi limiti — uzun xabarni qatorlar bo'yicha qisqartiradi."""
    if len(text) <= limit:
        return text
    lines, size = [], 0
    for line in text.split("\n"):
        if size + len(line) + 1 > limit:
            break
        lines.append(line)
        size += len(line) + 1
    lines.append("\n… <i>Natija uzun, qisqaroq davr tanlang.</i>")
    return "\n".join(lines)