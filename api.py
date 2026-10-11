import asyncio
from collections import defaultdict

from core.config import BASE_URL
from core.hemis import ApiError, get_all
from core.utils import attendance_absent, get_obj_value, to_number, unique_semesters
from core.timeutil import item_date, lesson_text

SEMESTERS = "/rest/v1/education/semesters"
SUBJECTS = "/rest/v1/education/subjects"
ATTENDANCE = "/rest/v1/education/attendance"


async def get_semesters(token):
    return unique_semesters(await get_all(BASE_URL, SEMESTERS, token, ttl=600))


def _parse_subject(item):
    if not isinstance(item, dict):
        return None

    # Yangi format: {"subject": {...}}, eski format: to'g'ridan-to'g'ri
    obj = item.get("subject") if isinstance(item.get("subject"), dict) else item

    name = get_obj_value(obj, "name", "title", "subject_name", "subjectName")
    if not name:
        return None

    return {
        "id": str(get_obj_value(obj, "id", "subject_id", "subjectId", default="")),
        "name": str(name).strip(),
        "code": str(get_obj_value(obj, "code", "subject_code", "subjectCode", default="")),
    }


async def get_subjects(token, semester_code):
    """Semestrdagi BARCHA fanlar (API semester CODE kutadi)."""
    items = await get_all(
        BASE_URL, SUBJECTS, token, {"semester": str(semester_code)}, ttl=600
    )

    unique, seen = [], set()
    for item in items:
        subject = _parse_subject(item)
        if not subject:
            continue
        key = subject["id"] or subject["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(subject)

    unique.sort(key=lambda s: s["name"].lower())
    return unique


def _attendance_subject_id(item):
    obj = item.get("subject")
    if isinstance(obj, dict):
        value = get_obj_value(obj, "id", "subject_id")
    else:
        value = get_obj_value(item, "subject_id", "subjectId")
    return str(value) if value is not None else None


async def _bulk_attendance(token, code):
    """Butun semestr davomati — BITTA so'rov."""
    try:
        return await get_all(BASE_URL, ATTENDANCE, token, {"semester": str(code)})
    except ApiError:
        return []  # TokenExpired bu yerda ushlanmaydi, yuqoriga ketadi


async def _subject_attendance(token, code, subject_id):
    try:
        return await get_all(
            BASE_URL,
            ATTENDANCE,
            token,
            {"subject": str(subject_id), "semester": str(code)},
        )
    except ApiError:
        return []


async def _per_subject_attendance(token, code, subjects):
    """Zaxira yo'l: har bir fan uchun PARALLEL so'rov."""
    valid = [s for s in subjects if s["id"]]
    results = await asyncio.gather(
        *(_subject_attendance(token, code, s["id"]) for s in valid)
    )
    return {s["id"]: items for s, items in zip(valid, results)}


def _group_by_subject(items):
    grouped = defaultdict(list)
    for item in items:
        if not isinstance(item, dict):
            continue
        subject_id = _attendance_subject_id(item)
        if subject_id:
            grouped[subject_id].append(item)
    return grouped


def _totals(items):
    absent = sum(attendance_absent(i) for i in items)
    present = sum(
        to_number(
            get_obj_value(
                i, "present", "present_hours", "presentHours", "attended", default=0
            )
        )
        for i in items
    )
    return {"absent": absent, "present": present}


async def load_semester_rows(token, semester):
    code = semester["code"]

    # Fanlar va davomat bir vaqtda olinadi
    subjects, bulk = await asyncio.gather(
        get_subjects(token, code),
        _bulk_attendance(token, code),
    )

    grouped = _group_by_subject(bulk)
    if not grouped and subjects:
        grouped = await _per_subject_attendance(token, code, subjects)

    rows = []
    for subject in subjects:
        rows.append({**subject, **_totals(grouped.get(subject["id"], []))})
    return rows


async def load_selected_semester(token, semester_id):
    semesters = await get_semesters(token)
    selected = next((s for s in semesters if s["id"] == str(semester_id)), None)
    if selected is None:
        return None, []
    return selected, await load_semester_rows(token, selected)


async def load_overall(token):
    semesters = await get_semesters(token)
    all_rows = await asyncio.gather(
        *(load_semester_rows(token, s) for s in semesters)
    )
async def load_daily(token, start, end):
    """[start, end] oralig'ida qoldirilgan darslar."""
    semesters = await get_semesters(token)

    # Barcha semestrlar davomati parallel (har biri BITTA so'rov)
    lists = await asyncio.gather(
        *(_bulk_attendance(token, s["code"]) for s in semesters)
    )

    rows, seen = [], set()
    for items in lists:
        for item in items:
            if not isinstance(item, dict):
                continue

            day = item_date(item)
            if day is None or not (start <= day <= end):
                continue

            hours = attendance_absent(item)
            if hours <= 0:
                continue

            subject = item.get("subject")
            if isinstance(subject, dict):
                name = get_obj_value(subject, "name", "title")
            else:
                name = get_obj_value(item, "subject_name", "subjectName")

            pair = lesson_text(item)
            key = item.get("id") or (day, name, pair, hours)
            if key in seen:
                continue
            seen.add(key)

            rows.append(
                {
                    "date": day,
                    "subject": str(name or "Noma'lum fan"),
                    "hours": hours,
                    "pair": pair,
                }
            )

    rows.sort(key=lambda r: (r["date"], r["pair"], r["subject"]))
    return rows

    return [
        {
            "name": semester["name"],
            "absent": sum(r["absent"] for r in rows),
            "subject_count": len(rows),
        }
        for semester, rows in zip(semesters, all_rows)
    ]