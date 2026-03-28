# -*- coding: utf-8 -*-
"""محرك حقن البيانات في القالب وتوليد الكراس"""

from io import BytesIO
from docx import Document
from .schedule import ROUTINE_ACTIVITIES


def _safe_replace(paragraph, old, new):
    if old not in paragraph.text:
        return False
    for run in paragraph.runs:
        if old in run.text:
            run.text = run.text.replace(old, new)
            return True
    full = paragraph.text.replace(old, new)
    if paragraph.runs:
        for run in paragraph.runs:
            run.text = ""
        paragraph.runs[0].text = full
    return True


def build_daily_planner_bytes(
    day: str,
    template_bytes: bytes,
    schedule: dict,
    lessons_db: dict,
    week_num: str = "",
    date_str: str = "",
) -> tuple:
    """
    بناء كراس يوم واحد

    Returns:
        (bytes_الكراس, قائمة_الحصص, قائمة_التحذيرات)
    """
    plan = schedule.get(day, [])
    if not plan:
        return None, [], [f"اليوم '{day}' غير موجود"]

    doc = Document(BytesIO(template_bytes))

    replacements = {
        "{{اليوم}}": day,
        "{{التاريخ}}": date_str,
        "{{الأسبوع}}": week_num,
    }

    sessions_info = []
    warnings = []

    for i, session in enumerate(plan, 1):
        act = session["النشاط"]
        dur = session["المدة"]
        period = session.get("الفترة", "")

        k_act = f"{{{{نشاط_{i}}}}}"
        k_top = f"{{{{موضوع_{i}}}}}"
        k_ind = f"{{{{كفاءة_{i}}}}}"
        k_dur = f"{{{{مدة_{i}}}}}"
        k_fld = f"{{{{ميدان_{i}}}}}"

        replacements[k_dur] = dur
        replacements[k_act] = act

        info = {
            "رقم": i,
            "النشاط": act,
            "المدة": dur,
            "الفترة": period,
            "نوع": "روتيني",
            "الموضوع": "—",
            "الكفاءة": "—",
        }

        if act in ROUTINE_ACTIVITIES:
            replacements[k_top] = "—"
            replacements[k_ind] = "—"
            replacements[k_fld] = "—"

        elif act in lessons_db and lessons_db[act]:
            lesson = lessons_db[act].pop(0)
            topic = lesson.get('موضوع', '—')
            indic = lesson.get('كفاءة', '—')

            replacements[k_top] = topic
            replacements[k_ind] = indic
            replacements[k_fld] = act

            info["نوع"] = "تعليمي"
            info["الموضوع"] = topic
            info["الكفاءة"] = indic

        else:
            replacements[k_top] = "⚠ لا توجد مذكرة"
            replacements[k_ind] = "⚠ لا توجد مذكرة"
            replacements[k_fld] = act
            info["نوع"] = "ناقص"
            warnings.append(act)

        sessions_info.append(info)

    # الحقن
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for k, v in replacements.items():
                        if k in para.text:
                            _safe_replace(para, k, str(v))

    for para in doc.paragraphs:
        for k, v in replacements.items():
            if k in para.text:
                _safe_replace(para, k, str(v))

    buf = BytesIO()
    doc.save(buf)

    return buf.getvalue(), sessions_info, warnings
