from core.utils import escape_text, format_hours
from core.timeutil import clip_message, fmt_date_full
from core.timeutil import clip_message, fmt_date_full


def build_group_summary(group_name, semester_name, rows):
    total = sum(r["absent"] for r in rows)
    return (
        f"👥 <b>{escape_text(group_name)}</b>\n"
        f"📚 {escape_text(semester_name)}\n\n"
        "Kerakli ko'rinishni tanlang:\n\n"
        f"👨‍🎓 Talabalar soni: <b>{len(rows)}</b>\n"
        f"🛑 Jami qoldirilgan: <b>{format_hours(total)} soat</b>"
    )


def build_students_report(group_name, semester_name, rows):
    header = f"👥 <b>{escape_text(group_name)}</b> · {escape_text(semester_name)}"

    if not rows:
        return f"{header}\n\n⚠️ Bu guruhda talabalar topilmadi."

    table_lines = ["№  Talaba                       Soat", "─" * 38]
    total = 0.0

    for i, row in enumerate(rows, 1):
        name = row["name"]
        if len(name) > 26:
            name = name[:25] + "…"
        total += row["absent"]
        table_lines.append(f"{i:<3}{name:<27}{format_hours(row['absent']):>6}")

    table = "\n".join(escape_text(line) for line in table_lines)

    return "\n".join(
        [
            header,
            "",
            "📌 <b>Talabalar bo'yicha davomat</b>",
            "",
            f"<pre>{table}</pre>",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🛑 <b>Jami qoldirilgan:</b> <b>{format_hours(total)} soat</b>",
        ]
    )


def build_group_total_report(group_name, semester_name, rows):
    total = sum(r["absent"] for r in rows)
    with_absence = sum(1 for r in rows if r["absent"] > 0)
    average = total / len(rows) if rows else 0.0

    return "\n".join(
        [
            f"📊 <b>{escape_text(group_name)}</b>",
            f"📚 {escape_text(semester_name)}",
            "",
            "📌 <b>Guruh bo'yicha umumiy davomat</b>",
            "",
            f"👨‍🎓 Talabalar soni: <b>{len(rows)}</b>",
            f"⚠️ Dars qoldirganlar: <b>{with_absence}</b>",
            f"🛑 Jami qoldirilgan: <b>{format_hours(total)} soat</b>",
            f"📉 O'rtacha (bir talabaga): <b>{format_hours(round(average, 2))} soat</b>",
            "",
            "👇 Batafsil ko'rish uchun «Talabalar bo'yicha» tugmasini bosing.",
        ]
    )


def build_overall_report(group_reports):
    if not group_reports:
        return "⚠️ Umumiy davomat ma'lumotlari topilmadi."

    lines = ["📊 <b>Umumiy davomat</b>", "📌 Barcha guruhlar bo'yicha", ""]
    total = 0.0

    for r in group_reports:
        total += r["absent"]
        lines += [
            f"👥 <b>{escape_text(r['name'])}</b>",
            f"   Talabalar: <b>{r['students']}</b>",
            f"   🛑 Qoldirilgan: <b>{format_hours(r['absent'])} soat</b>",
            "",
        ]

    lines += [
        "━━━━━━━━━━━━━━━━━━",
        f"🛑 <b>Jami qoldirilgan:</b> <b>{format_hours(total)} soat</b>",
    ]
    return "\n".join(lines)
def build_daily_report(group_name, title, rows):
    head = f"👥 <b>{escape_text(group_name)}</b>\n📅 <b>{escape_text(title)}</b>"

    if not rows:
        return (
            f"{head}\n\n✅ Bu davrda dars qoldirgan talaba yo'q.\n\n"
            "ℹ️ <i>Ma'lumot HEMIS'ga davomat kiritilgandan keyin chiqadi.</i>"
        )

    lines = [head, ""]
    current_date = None
    total = 0.0

    for row in rows:
        if row["date"] != current_date:
            current_date = row["date"]
            if len(lines) > 2:
                lines.append("")
            lines.append(f"📆 <b>{fmt_date_full(current_date)}</b>")

        total += row["hours"]
        extra = f" · {escape_text(row['pair'])}" if row["pair"] else ""
        lines.append(
            f"  • {escape_text(row['student'])} — {escape_text(row['subject'])}: "
            f"<b>{format_hours(row['hours'])} soat</b>{extra}"
        )

    students = len({r["student"] for r in rows})
    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        f"👨‍🎓 Dars qoldirgan talabalar: <b>{students}</b>",
        f"🛑 <b>Jami qoldirilgan:</b> <b>{format_hours(total)} soat</b>",
    ]
    return clip_message("\n".join(lines))
