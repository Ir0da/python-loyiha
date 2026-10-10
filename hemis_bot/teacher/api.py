import asyncio
from collections import defaultdict

from core.config import TEACHER_BASE_URL
from core.hemis import get_all
from core.utils import attendance_absent, get_obj_value, unique_semesters
from core.timeutil import item_date, lesson_text
from core.timeutil import item_date, lesson_text
# =====================================================================
# DIQQAT: bu yo'llar va filtr nomlari taxminiy.
# HEMIS API hujjatidan (Swagger) tekshirib, kerak bo'lsa FAQAT shu
# yerni o'zgartiring — kodning qolgan qismi o'zgarmaydi.
# =====================================================================
PATHS = {
    "groups": "/rest/v1/data/group-list",
    "students": "/rest/v1/data/student-list",
    "semesters": "/rest/v1/data/semester-list",
    "attendance": "/rest/v1/data/student-attendance-list",
}
FILTER_GROUP = "_group"
FILTER_SEMESTER = "_semester"

BASE = TEACHER_BASE_URL


async def get_groups(token):
    items = await get_all(BASE, PATHS["groups"], token, ttl=600)

    groups = []
    for item in items:
        group_id = get_obj_value(item, "id", "group_id")
        name = get_obj_value(item, "name", "title")
        if group_id is None or not name:
            continue
        groups.append({"id": str(group_id), "name": str(name)})

    groups.sort(key=lambda g: g["name"].lower())
    return groups


async def get_semesters(token):
    return unique_semesters(await get_all(BASE, PATHS["semesters"], token, ttl=600))


def _student_name(item):
    obj = item.get("student") if isinstance(item.get("student"), dict) else item

    name = get_obj_value(obj, "full_name", "fullName", "name")
    if name:
        return str(name).strip()

    parts = [get_obj_value(obj, k, default="") for k in ("second_name", "first_name", "third_name")]
    return " ".join(str(p) for p in parts if p).strip() or "Noma'lum"


def _student_id(item):
    obj = item.get("student")
    if isinstance(obj, dict):
        value = get_obj_value(obj, "id", "student_id")
    else:
        value = get_obj_value(item, "student_id", "studentId", "id")
    return str(value) if value is not None else None


async def get_students(token, group_id):
    items = await get_all(
        BASE, PATHS["students"], token, {FILTER_GROUP: group_id}, ttl=600
    )

    students, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue
        student_id = _student_id(item)
        if not student_id or student_id in seen:
            continue
        seen.add(student_id)
        students.append({"id": student_id, "name": _student_name(item)})
    return students


async def fetch_group_absent(token, group_id, semester_code=None):
    """Guruh davomati — BITTA so'rov. {student_id: soat}"""
    params = {FILTER_GROUP: group_id}
    if semester_code is not None:
        params[FILTER_SEMESTER] = str(semester_code)

    items = await get_all(BASE, PATHS["attendance"], token, params)

    absent = defaultdict(float)
    for item in items:
        if not isinstance(item, dict):
            continue
        student_id = _student_id(item)
        if student_id:
            absent[student_id] += attendance_absent(item)
    return absent


async def load_group_semester(token, group_id, semester_id):
    groups, semesters = await asyncio.gather(get_groups(token), get_semesters(token))

    group = next((g for g in groups if g["id"] == str(group_id)), None)
    semester = next((s for s in semesters if s["id"] == str(semester_id)), None)
    if group is None or semester is None:
        return None, None, []

    # Talabalar ro'yxati va davomat bir vaqtda olinadi
    students, absent = await asyncio.gather(
        get_students(token, group["id"]),
        fetch_group_absent(token, group["id"], semester["code"]),
    )

    rows = [
        {"id": s["id"], "name": s["name"], "absent": absent.get(s["id"], 0.0)}
        for s in students
    ]
    rows.sort(key=lambda r: (-r["absent"], r["name"].lower()))
    return group, semester, rows


async def _group_summary(token, group):
    students, absent = await asyncio.gather(
        get_students(token, group["id"]),
        fetch_group_absent(token, group["id"]),
    )
    return {
        "name": group["name"],
        "students": len(students),
        "absent": sum(absent.values()),
    }


async def load_overall(token):
    groups = await get_groups(token)
    return list(await asyncio.gather(*(_group_summary(token, g) for g in groups)))
async def load_group_daily(token, group_id, start, end):
    """Guruhda [start, end] oralig'ida dars qoldirgan talabalar."""
    groups = await get_groups(token)
    group = next((g for g in groups if g["id"] == str(group_id)), None)
    if group is None:
        return None, []

    students, items = await asyncio.gather(
        get_students(token, group["id"]),
        get_all(BASE, PATHS["attendance"], token, {FILTER_GROUP: group["id"]}),
    )
    names = {s["id"]: s["name"] for s in students}

    rows, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue

        day = item_date(item)
        if day is None or not (start <= day <= end):
            continue

        hours = attendance_absent(item)
        if hours <= 0:
            continue

        student_id = _student_id(item)
        name = names.get(student_id) or _student_name(item)

        subject = item.get("subject")
        if isinstance(subject, dict):
            subject_name = get_obj_value(subject, "name", "title")
        else:
            subject_name = get_obj_value(item, "subject_name", "subjectName")

        pair = lesson_text(item)
        key = item.get("id") or (day, student_id, subject_name, pair, hours)
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            {
                "date": day,
                "student": name,
                "subject": str(subject_name or "Noma'lum fan"),
                "hours": hours,
                "pair": pair,
            }
        )

    rows.sort(key=lambda r: (r["date"], r["student"].lower(), r["pair"]))
    return group, rows
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
async def load_group_daily(token, group_id, start, end):
    """Guruhda [start, end] oralig'ida dars qoldirgan talabalar."""
    groups = await get_groups(token)
    group = next((g for g in groups if g["id"] == str(group_id)), None)
    if group is None:
        return None, []

    students, items = await asyncio.gather(
        get_students(token, group["id"]),
        get_all(BASE, PATHS["attendance"], token, {FILTER_GROUP: group["id"]}),
    )
    names = {s["id"]: s["name"] for s in students}

    rows, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue

        day = item_date(item)
        if day is None or not (start <= day <= end):
            continue

        hours = attendance_absent(item)
        if hours <= 0:
            continue

        student_id = _student_id(item)
        name = names.get(student_id) or _student_name(item)

        subject = item.get("subject")
        if isinstance(subject, dict):
            subject_name = get_obj_value(subject, "name", "title")
        else:
            subject_name = get_obj_value(item, "subject_name", "subjectName")

        pair = lesson_text(item)
        key = item.get("id") or (day, student_id, subject_name, pair, hours)
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            {
                "date": day,
                "student": name,
                "subject": str(subject_name or "Noma'lum fan"),
                "hours": hours,
                "pair": pair,
            }
        )

    rows.sort(key=lambda r: (r["date"], r["student"].lower(), r["pair"]))
    return group, rows