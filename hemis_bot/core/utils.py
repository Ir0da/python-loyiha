import html


def escape_text(value):
    return html.escape(str(value))


def to_number(value):
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def format_hours(value):
    number = to_number(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def get_obj_value(obj, *keys, default=None):
    if not isinstance(obj, dict):
        return default
    for key in keys:
        value = obj.get(key)
        if value is not None:
            return value
    return default


_LIST_KEYS = ("data", "items", "results", "semesters", "subjects", "attendance")


def extract_list(payload, keys=_LIST_KEYS):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = extract_list(value, keys)
            if nested:
                return nested

    for value in payload.values():
        if isinstance(value, list):
            return value
    return []


def page_count(payload):
    """HEMIS: {"data": {"items": [...], "pagination": {"pageCount": N}}}"""
    data = payload.get("data") if isinstance(payload, dict) else None
    pagination = data.get("pagination") if isinstance(data, dict) else None
    try:
        return int(pagination.get("pageCount", 1))
    except (AttributeError, TypeError, ValueError):
        return 1


def normalize_semester_item(item):
    if not isinstance(item, dict):
        return None

    inner = item.get("semester")

    def pick(*keys):
        value = get_obj_value(item, *keys)
        if value is None:
            value = get_obj_value(inner, *keys)
        return value

    semester_id = pick("id", "semester_id", "semesterId")
    if semester_id is None:
        return None

    code = pick("code", "semester_code", "semesterCode")
    if code is None:
        code = semester_id

    name = pick("name", "title", "semester_name", "semesterName")
    if not name:
        name = f"{code}-semestr"

    return {"id": str(semester_id), "code": str(code), "name": str(name)}


def unique_semesters(items):
    result, seen = [], set()
    for item in items:
        sem = normalize_semester_item(item)
        if not sem:
            continue
        key = (sem["id"], sem["code"])
        if key in seen:
            continue
        seen.add(key)
        result.append(sem)
    return result


def attendance_absent(item):
    """Bitta davomat yozuvidagi qoldirilgan soat."""
    if not isinstance(item, dict):
        return 0.0

    total = get_obj_value(item, "absent", "absent_hours", "absentHours")
    if total is not None and to_number(total) > 0:
        return to_number(total)

    return (
        to_number(get_obj_value(item, "absent_off", "absentOff", default=0))
        + to_number(get_obj_value(item, "absent_on", "absentOn", default=0))
    )