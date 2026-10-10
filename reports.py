from core.utils import escape_text, format_hours, to_number
from core.timeutil import clip_message, fmt_date_full


def semester_totals(subjects):
    return {
        "absent": sum(to_number(s.get("absent", 0)) for s in subjects),
        "present": sum(to_number(s.get("present", 0)) for s in subjects),
    }


def build_semester_summary(semester_name, subjects):
    totals = semester_totals(subjects)
    return (
        f"📚 <b>{escape_text(semester_name)}</b>\n\n"
        "Kerakli ko'rinishni tanlang:\n\n"
        f"📚 Fanlar soni: <b>{len(subjects)}</b>\n"
        f"🛑 Jami qoldirilgan: <b>{format_hours(totals['absent'])} soat</b>"
    )


def build_subject_report(semester_name, subject_rows):
    if not subject_rows:
        return (
            f"📚 <b>{escape_text(semester_name)}</b>\n\n"
            "⚠️ Bu semestrda fanlar topilmadi."
        )

    table_lines = ["Fan                             Soat", "─" * 36]
    total_absent = 0.0

    for row in subject_rows:
        name = row["name"]
        if len(name) > 30:
            name = name[:29] + "…"
        total_absent += row["absent"]
        table_lines.append(f"{name:<30}{format_hours(row['absent']):>6}")

    table = "\n".join(escape_text(line) for line in table_lines)

    return "\n".join(
        [
            f"📚 <b>{escape_text(semester_name)}</b>",
            "",
            "📌 <b>Fanlar bo'yicha davomat</b>",
            "",
            f"<pre>{table}</pre>",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🛑 <b>Jami qoldirilgan:</b> <b>{format_hours(total_absent)} soat</b>",
        ]
    )


def build_semester_total_report(semester_name, subjects):
    totals = semester_totals(subjects)

    lines = [
        f"📊 <b>{escape_text(semester_name)}</b>",
        "",
        "📌 <b>Semestr bo'yicha umumiy davomat</b>",
        "",
        f"📚 Fanlar soni: <b>{len(subjects)}</b>",
        f"🛑 Qoldirilgan soat: <b>{format_hours(totals['absent'])}</b>",
    ]
    if totals["present"] > 0:
        lines.append(
            f"✅ Davomat qilingan soat: <b>{format_hours(totals['present'])}</b>"
        )
    lines += ["", "👇 Batafsil ko'rish uchun «Fanlar bo'yicha» tugmasini bosing."]
    return "\n".join(lines)


def build_overall_report(semester_reports):
    if not semester_reports:
        return "⚠️ Umumiy davomat ma'lumotlari topilmadi."

    lines = ["📊 <b>Umumiy davomat</b>", "📌 Barcha semestrlar bo'yicha", ""]
    total = 0.0

    for r in semester_reports:
        total += r["absent"]
        lines += [
            f"📚 <b>{escape_text(r['name'])}</b>",
            f"   Fanlar: <b>{r['subject_count']}</b>",
            f"   🛑 Qoldirilgan: <b>{format_hours(r['absent'])} soat</b>",
            "",
        ]

    lines += [
        "━━━━━━━━━━━━━━━━━━",
        f"🛑 <b>Jami qoldirilgan:</b> <b>{format_hours(total)} soat</b>",
    ]
    return "\n".join(lines)
def build_daily_report(title, rows):
    head = f"📅 <b>{escape_text(title)}</b>"

    if not rows:
        return (
            f"{head}\n\n"
            "✅ Bu davrda qoldirilgan dars yo'q.\n\n"
            "ℹ️ <i>Ma'lumot HEMIS'ga o'qituvchi davomatni "
            "kiritgandan keyin chiqadi.</i>"
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
            f"  • {escape_text(row['subject'])} — "
            f"<b>{format_hours(row['hours'])} soat</b>{extra}"
        )

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🛑 <b>Jami qoldirilgan:</b> <b>{format_hours(total)} soat</b>",
    ]
    return clip_message("\n".join(lines))